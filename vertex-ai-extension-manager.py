# TODO: UNDER DEVELOPMENT

import json

from google.api_core import exceptions

from google.cloud.aiplatform_v1beta1 import ExtensionRegistryServiceClient
from google.cloud.aiplatform_v1beta1.types import (
    extension as gca_extension_types,
    extension_registry_service,
)
from google.protobuf import json_format
from google.protobuf.struct_pb2 import Struct


def _get_api_endpoint(location: str) -> str:
    """Gets the regional API endpoint for the given location."""
    return f"{location}-aiplatform.googleapis.com"


def export_extension_to_file(name: str, output_file: str = "extension_config.json"):
    """
    Fetches an existing Vertex AI Extension and saves its configuration to a JSON file.

    Args:
        name (str): The full resource name of the extension.
                    Format: projects/{p}/locations/{l}/extensions/{e}
        output_file (str): The path to save the JSON configuration file.
    """
    print(f"Attempting to export extension: {name}")
    try:
        # Extract location from the full resource name to configure the client
        location = name.split("/")[3]
        api_endpoint = _get_api_endpoint(location)

        # Create a client for the Extension Registry Service from the v1beta1 API
        client = ExtensionRegistryServiceClient(
            client_options={"api_endpoint": api_endpoint}
        )

        # Prepare the request using the correct type from extension_registry_service
        request = extension_registry_service.GetExtensionRequest(name=name)

        # Make the API call to fetch the extension
        extension_proto = client.get_extension(request=request)
        print("Successfully fetched extension details.")

        # Convert the protobuf object to a dictionary.
        extension_dict = json.loads(json_format.MessageToJson(extension_proto._pb))

        # Save the dictionary to a JSON file
        with open(output_file, "w") as f:
            json.dump(extension_dict, f, indent=4)

        print(f"✅ Extension configuration successfully saved to '{output_file}'")

    except exceptions.NotFound:
        print(
            f"❌ Error: Extension not found at '{name}'. Please check the resource name."
        )
    except Exception as e:
        print(f"❌ An unexpected error occurred during export: {e}")


def create_extension_from_file(
    project_id: str,
    location: str,
    config_file: str = "extension_config.json",
    new_display_name: str = "My Replicated Extension",
    service_directory_override: str | None = None,
):
    """
    Creates a new Vertex AI Extension from a configuration file.

    Args:
        project_id (str): Your Google Cloud project ID.
        location (str): The GCP region for the new extension (e.g., 'us-central1').
        config_file (str): The path to the JSON configuration file.
        new_display_name (str, optional): A new display name for the created extension.
                                          If None, uses the name from the config file.
        service_directory_override (str, optional): The full resource name of the Service Directory.
                                                    This is required if the extension uses PSC, as this
                                                    value is not exported by the GetExtension API.
    """
    print(
        f"Attempting to create extension from '{config_file}' in project '{project_id}'..."
    )
    try:
        # Load the configuration from the file
        with open(config_file, "r") as f:
            config_dict = json.load(f)
        print("Successfully loaded configuration file.")

        if "privateServiceConnectConfig" in config_dict:
            psc_config = config_dict["privateServiceConnectConfig"]
            # If an override is provided, inject it into the config.
            if service_directory_override:
                print(
                    f"Injecting provided service directory: {service_directory_override}"
                )
                # Ensure psc_config is a dictionary before assignment
                if not isinstance(psc_config, dict):
                    psc_config = {}
                psc_config["serviceDirectory"] = service_directory_override
                config_dict["privateServiceConnectConfig"] = psc_config
            # If no override is given and the key is still missing, raise an error.
            elif not psc_config or not psc_config.get("serviceDirectory"):
                print(
                    "\n❌ Critical Error: The exported configuration has an empty 'privateServiceConnectConfig'."
                )
                print(
                    "   The 'serviceDirectory' value is required for creation but is not exported by the API."
                )
                print(
                    "   Please provide the full Service Directory resource name (e.g., projects/.../locations/.../namespaces/.../services/...)"
                )
                print(
                    "   by setting the 'MANUAL_SERVICE_DIRECTORY' variable in the script."
                )
                return  # Stop execution to prevent the API error.

        # --- Prepare the Extension object for creation ---
        # Remove output-only fields that the API will generate.
        output_only_fields = ["name", "createTime", "updateTime", "etag"]
        for field in output_only_fields:
            config_dict.pop(field, None)

        # Update display name if a new one is provided
        if new_display_name:
            config_dict["displayName"] = new_display_name
            print(f"Using new display name: '{new_display_name}'")

        # Use ParseDict to convert the Python dictionary directly into a protobuf message.
        extension_to_create = json_format.ParseDict(
            config_dict, gca_extension_types.Extension()._pb
        )

        # --- Make the API call to create the extension ---
        api_endpoint = _get_api_endpoint(location)
        client = ExtensionRegistryServiceClient(
            client_options={"api_endpoint": api_endpoint}
        )

        parent = f"projects/{project_id}/locations/{location}"

        # Use the ImportExtension method, with the request type from extension_registry_service
        request = extension_registry_service.ImportExtensionRequest(
            parent=parent,
            extension=extension_to_create,
        )

        # The API call returns a long-running operation
        operation = client.import_extension(request=request)
        print("Extension creation initiated. Waiting for operation to complete...")

        # Wait for the operation to complete and get the result
        created_extension = operation.result()

        # Check if the operation returned a result before trying to access its attributes.
        if created_extension:
            print("\n🎉 Successfully created new extension!")
            print(f"   Resource Name: {created_extension.name}")
            print(f"   Display Name: {created_extension.display_name}")
        else:
            print(
                "\n❌ Extension creation operation completed, but no result was returned."
            )

    except FileNotFoundError:
        print(f"❌ Error: Configuration file not found at '{config_file}'.")
    except Exception as e:
        print(f"❌ An unexpected error occurred during creation: {e}")


# --- Main execution block ---
if __name__ == "__main__":
    # --- Configuration ---
    # TODO: Fill in your project and location details.
    PROJECT_ID = ""
    LOCATION = "us-central1"

    # The full resource name of the extension to be copied.
    EXISTING_EXTENSION_NAME = (
        f"projects/{PROJECT_ID}/locations/{LOCATION}/extensions/4685957204249935872"
    )

    # The file to store the configuration.
    CONFIG_FILE = "my_extension_backup.json"

    # TODO: If your extension uses Private Service Connect, you MUST provide this value.
    # Format: "projects/{project-id}/locations/{location}/namespaces/{namespace-id}/services/{service-id}"
    MANUAL_SERVICE_DIRECTORY = "projects/your-project/locations/us-central1/namespaces/your-namespace/services/your-service"  # <-- REPLACE THIS or set to None

    # --- Step 1: Export the existing extension ---
    # This will read the extension from Vertex AI and save it to CONFIG_FILE.
    print("--- Step 1: Exporting Extension ---")
    export_extension_to_file(name=EXISTING_EXTENSION_NAME, output_file=CONFIG_FILE)
    print("-" * 35)

    # --- Step 2: Create a new extension from the file ---
    # This will read the CONFIG_FILE and create a new extension.
    # You can give it a new name to avoid conflicts.
    print("\n--- Step 2: Creating New Extension ---")
    create_extension_from_file(
        project_id=PROJECT_ID,
        location=LOCATION,
        config_file=CONFIG_FILE,
        new_display_name="My Replicated Extension",
        service_directory_override=MANUAL_SERVICE_DIRECTORY,
    )
    print("-" * 35)

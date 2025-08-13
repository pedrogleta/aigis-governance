import base64
import json
from pathlib import Path


def load_artifact_from_inline_data(inline_data_dict, output_path=None):
    """
    Convert inline data format to a valid PNG file.

    Args:
        inline_data_dict (dict): Dictionary with format:
            {"inlineData": {"data": "iVBORw0...", "mimeType": "image/png"}}
        output_path (str, optional): Path where to save the PNG file.
            If None, saves as 'artifact.png' in current directory.

    Returns:
        str: Path to the created PNG file

    Raises:
        ValueError: If the data format is invalid or mime type is not image/png
        Exception: If there's an error decoding or writing the file
    """
    try:
        # Extract inline data
        if "inlineData" not in inline_data_dict:
            raise ValueError("Missing 'inlineData' key in dictionary")

        inline_data = inline_data_dict["inlineData"]

        if "data" not in inline_data or "mimeType" not in inline_data:
            raise ValueError("Missing 'data' or 'mimeType' in inlineData")

        data = inline_data["data"]
        mime_type = inline_data["mimeType"]

        # Validate mime type
        if mime_type != "image/png":
            raise ValueError(f"Expected mime type 'image/png', got '{mime_type}'")

        # Decode base64 data
        try:
            decoded_data = base64.b64decode(data)
        except Exception as e:
            raise ValueError(f"Invalid base64 data: {e}")

        # Set output path
        if output_path is None:
            output_path = "artifact.png"

        # Ensure output directory exists
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Write PNG file
        with open(output_file, "wb") as f:
            f.write(decoded_data)

        print(f"PNG file created successfully at: {output_file.absolute()}")
        return str(output_file.absolute())

    except Exception as e:
        raise Exception(f"Error creating PNG file: {e}")


def load_artifact_from_json_file(json_file_path, output_path=None):
    """
    Load artifact from a JSON file and convert to PNG.

    Args:
        json_file_path (str): Path to JSON file containing inline data
        output_path (str, optional): Path where to save the PNG file

    Returns:
        str: Path to the created PNG file
    """
    try:
        with open(json_file_path, "r") as f:
            data_dict = json.load(f)

        return load_artifact_from_inline_data(data_dict, output_path)

    except Exception as e:
        raise Exception(f"Error reading JSON file: {e}")


# Example usage
if __name__ == "__main__":
    # Example with inline data
    example_data = {
        "inlineData": {
            "data": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==",
            "mimeType": "image/png",
        }
    }

    try:
        result = load_artifact_from_inline_data(example_data)
        print(f"Success! File created at: {result}")
    except Exception as e:
        print(f"Error: {e}")

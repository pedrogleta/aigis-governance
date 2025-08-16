import base64
import uuid
import os
from dotenv import load_dotenv
from minio import Minio
from minio.error import S3Error

# Load environment variables from .env file
load_dotenv(override=True)


def execute_python(code_raw: str) -> str:
    """
    Executes python code and extracts artifacts like matplotlib plots for displaying to the user

    Args:
        code_raw (str): The raw code to be executed. NOTHING except just the code that will be run.

    Returns:
        str: stdout, stderr and number of plots generated if any
    """

    from llm_sandbox import ArtifactSandboxSession

    with ArtifactSandboxSession(lang="python") as session:
        result = session.run(
            code_raw,
            libraries=["io", "math", "re", "matplotlib", "numpy", "pandas", "scipy"],
        )

        response = f"""
        stdout: {result.stdout}
        stderr: {result.stderr}
        plots: {len(result.plots)}
        """

        # Initialize MinIO client with environment variables
        minio_host = os.getenv("MINIO_HOST", "localhost")
        minio_user = os.getenv("MINIO_ROOT_USER", "minioadmin")
        minio_password = os.getenv("MINIO_ROOT_PASSWORD", "minioadmin")

        minio_client = Minio(
            f"{minio_host}:9000",
            access_key=minio_user,
            secret_key=minio_password,
            secure=False,
        )

        # Ensure bucket exists
        bucket_name = "aigis-data-governance"
        try:
            if not minio_client.bucket_exists(bucket_name):
                minio_client.make_bucket(bucket_name)
        except S3Error as e:
            print(f"Error creating bucket: {e}")

        # Store plots in MinIO with random UUID names
        plot_urls = []
        for i, plot in enumerate(result.plots):
            # Generate random UUID for filename
            plot_uuid = str(uuid.uuid4())
            plot_filename = f"{plot_uuid}.{plot.format.value}"

            try:
                # Upload plot to MinIO
                plot_data = base64.b64decode(plot.content_base64)
                from io import BytesIO

                minio_client.put_object(
                    bucket_name,
                    plot_filename,
                    BytesIO(plot_data),
                    length=len(plot_data),
                    content_type=f"image/{plot.format.value}",
                )

                # Store the filename for reference
                plot_urls.append(plot_filename)

            except S3Error as e:
                print(f"Error uploading plot {i + 1}: {e}")

        # Add plot URLs to response if any were uploaded
        if plot_urls:
            response += f"\nplot_files: {','.join(plot_urls)}"

        return response

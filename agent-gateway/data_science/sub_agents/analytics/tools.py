import re
import base64
import uuid
import os
import io
from contextlib import redirect_stderr, redirect_stdout
from dotenv import load_dotenv
from minio import Minio
from minio.error import S3Error

load_dotenv(override=True)


def execute_python(code_raw: str) -> str:
    """
    Executes python code and extracts artifacts like matplotlib plots for displaying to the user

    Args:
        code_raw (str): The raw code to be executed. NOTHING except just the code that will be run.

    Returns:
        str: stdout, stderr and number of plots generated if any
    """

    # Check for all instances of ".show()" and collect the word directly connected to it

    plot_names = re.findall(r"(\w+)\.show\(\)", code_raw)
    plot_codes = []

    if len(plot_names) > 0:
        code_raw = "import io\nimport matplotlib.pyplot as plt\n" + code_raw

        for plot_name in plot_names:
            code_raw = code_raw.replace(plot_name + ".show()", "")

            plot_code = plot_name + "-" + str(uuid.uuid4())
            plot_codes.append(plot_code)

            # Writes plots to generated_plots
            # Can be upgraded to
            code_raw = (
                code_raw
                + f"""\n
buf = io.BytesIO()
plt.savefig(buf, format='png')
buf.seek(0)
b64_string = base64.b64encode(buf.getvalue()).decode('utf-8')
with open("./generated_plots/{plot_code}.txt", "w") as f:
    f.write(b64_string) 
"""
            )

    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()

    # @@TODO add logging for code generated and executed

    with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
        exec(code_raw)

    response = f"""
    stdout: {stdout_capture.getvalue().strip()}
    stderr: {stderr_capture.getvalue().strip()}
    generated {len(plot_names)} plots
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

    for plot_code in plot_codes:
        plot_file_path = f"./generated_plots/{plot_code}.txt"
        with open(plot_file_path, "r") as f:
            plot_data = f.read()

            plot_filename = f"{plot_code}.png"

            # Decode the base64 image data
            plot_bytes = base64.b64decode(plot_data)

            # Upload the image to MinIO
            try:
                minio_client.put_object(
                    bucket_name,
                    plot_filename,
                    io.BytesIO(plot_bytes),
                    length=len(plot_bytes),
                    content_type="image/png",
                )
            except S3Error as e:
                print(f"Error uploading plot to MinIO: {e}")
        os.remove(plot_file_path)

    return response

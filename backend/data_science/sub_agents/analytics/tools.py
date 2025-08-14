import base64
from pathlib import Path
from llm_sandbox import ArtifactSandboxSession


def execute_python(code_raw: str) -> str:
    """
    Executes python code and extracts artifacts like matplotlib plots for displaying to the user

    Args:
        code_raw (str): The raw code to be executed. NOTHING except just the code that will be run.

    Returns:
        str: stdout, stderr and number of plots generated if any
    """

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

        for i, plot in enumerate(result.plots):
            plot_path = Path(f"plot_{i + 1}.{plot.format.value}")
            with plot_path.open("wb") as f:
                f.write(base64.b64decode(plot.content_base64))

        return response

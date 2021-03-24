import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="kulcli", # Replace with your own username
    version="0.0.5",
    author="Jihwan Yuk",
    author_email="luzhcs@kulcloud.net",
    description="Python based Kulcloud CLI",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/luzhcs/kul-cli-py.git",
    packages=setuptools.find_packages(),
    python_requires='>=3.6',
    scripts=['kulcli/scripts/kulcli']
)
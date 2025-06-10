from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="tracegen",
    version="1.0.0",
    author="liumoulu",
    author_email="liumoulu@lixiang.com",
    description="标准格式 Trace 生成工具，将原始数据一键转为 Perfetto trace 文件",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/merlotliu/tracegen",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development",
        "Topic :: System :: Systems Administration",
        "Topic :: Utilities",
    ],
    python_requires=">=3.8",
    install_requires=[
        "protobuf>=3.20.0,<4.0.0",
        "requests",
        "click",
    ],
    entry_points={
        "console_scripts": [
            "tracegen=tracegen.cli:cli",
        ],
    },
    include_package_data=True,
    package_data={
        "tracegen": ["../configs/*.json"],
    },
) 
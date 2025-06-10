class Tracegen < Formula
  include Language::Python::Virtualenv

  desc "标准格式 Trace 生成工具，将原始数据一键转为 Perfetto trace 文件"
  homepage "https://github.com/merlotliu/tracegen"
  url "https://files.pythonhosted.org/packages/source/t/tracegen/tracegen-1.0.0.tar.gz"  # 这会在您发布到 PyPI 后自动生成
  sha256 "3cc8d23edfda9963d02920d38933e45257b039b82deff48cd983d8d5d7fd7e89"
  license "MIT"

  depends_on "python@3.11"

  resource "click" do
    url "https://files.pythonhosted.org/packages/source/c/click/click-8.1.8.tar.gz"
    sha256 "ed53c9d8990d83c2a27deae68e4ee337473f6330c040a31d4225c9574d16096a"
  end

  resource "protobuf" do
    url "https://files.pythonhosted.org/packages/source/p/protobuf/protobuf-5.31.0.tar.gz"
    sha256 "d1cf4c6c7abed4d8452235b5f7a96e8e5f0d3e0a8700e0c3b1c7b6b8b7b1d4df"
  end

  resource "requests" do
    url "https://files.pythonhosted.org/packages/source/r/requests/requests-2.32.4.tar.gz"
    sha256 "e7b2fb6d65f8c7e7e9c2e09ad4a73b5b2e88ff8d5d61cf0eff3a9c5c6e7e8b9a"
  end

  def install
    virtualenv_install_with_resources
  end

  test do
    system "#{bin}/tracegen", "--help"
  end
end 
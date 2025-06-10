class Tracegen < Formula
  include Language::Python::Virtualenv

  desc "标准格式 Trace 生成工具，支持多语言组件"
  homepage "https://gitlab.lixiang.com/tools/tracegen"
  url "https://gitlab.lixiang.com/tools/tracegen/-/archive/v1.0.0/tracegen-v1.0.0.tar.gz"
  sha256 "SHA256_FROM_GITLAB_RELEASE"  # 将通过 CI/CD 自动替换
  license "MIT"

  depends_on "python@3.11"
  
  # 构建时依赖（仅在有对应组件时需要）
  depends_on "rust" => :build if Dir.exist?("rust-components")
  depends_on "cmake" => :build if Dir.exist?("cpp-components")
  depends_on "gcc" => :build if Dir.exist?("cpp-components")

  resource "protobuf" do
    url "https://files.pythonhosted.org/packages/source/p/protobuf/protobuf-3.20.3.tar.gz"
    sha256 "2e3427429c9cffebf259491be0af70189607f365c2f41c7c3764af6f337105f2"
  end

  resource "requests" do
    url "https://files.pythonhosted.org/packages/source/r/requests/requests-2.32.4.tar.gz"
    sha256 "7dd5854b2dcaaf7a74e72c5ba77b9c9f43c8298d24abef59ddf8c7bc8f1e5e83"
  end

  resource "click" do
    url "https://files.pythonhosted.org/packages/source/c/click/click-8.2.1.tar.gz"
    sha256 "f16723e042e4440b547ad3d3fbb98dcc3e0b5cc5db42ccff6a1c3c16fba7f5a1"
  end

  def install
    # 构建 Rust 组件（如果存在）
    if Dir.exist?("rust-components")
      cd "rust-components" do
        system "cargo", "build", "--release"
        # 安装 Rust 生成的二进制文件
        Dir["target/release/*"].each do |file|
          if File.executable?(file) && File.file?(file)
            bin.install file
          end
        end
      end
    end

    # 构建 C++ 组件（如果存在）
    if Dir.exist?("cpp-components")
      cd "cpp-components" do
        system "cmake", ".", "-DCMAKE_INSTALL_PREFIX=#{prefix}", "-DCMAKE_BUILD_TYPE=Release"
        system "make", "install"
      end
    end

    # 安装 Python 组件
    virtualenv_install_with_resources
    
    # 确保配置文件也被安装
    if Dir.exist?("configs")
      (share/"tracegen").install Dir["configs/*"]
    end
  end

  test do
    system "#{bin}/tracegen", "--help"
    
    # 测试基本功能
    output = shell_output("#{bin}/tracegen --help 2>&1")
    assert_match "标准格式 Trace 生成工具", output
  end
end 
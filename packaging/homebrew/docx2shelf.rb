class Docx2shelf < Formula
  include Language::Python::Virtualenv

  desc "Offline CLI to convert DOCX manuscripts into valid EPUB 3"
  homepage "https://github.com/LightWraith8268/Docx2Shelf"
  url "https://files.pythonhosted.org/packages/source/d/docx2shelf/docx2shelf-1.0.9.tar.gz"
  sha256 "TO_BE_UPDATED"  # This will be updated automatically when publishing
  license "MIT"

  depends_on "python@3.11"
  depends_on "pandoc" => :optional

  resource "ebooklib" do
    url "https://files.pythonhosted.org/packages/source/e/ebooklib/ebooklib-0.18.tar.gz"
    sha256 "TO_BE_UPDATED"
  end

  def install
    virtualenv_install_with_resources
  end

  test do
    system "#{bin}/docx2shelf", "--help"

    # Test basic functionality
    (testpath/"test.md").write("# Test Document\n\nThis is a test.")
    system "#{bin}/docx2shelf", "build", "--input", "test.md", "--title", "Test", "--author", "Test Author", "--no-prompt"

    assert_predicate testpath.glob("*.epub").first, :exist?
  end
end
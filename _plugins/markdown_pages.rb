# Compiled wiki pages have no front matter; render every Markdown file as a
# page (layout comes from the _config.yml defaults) instead of copying it.
module Jekyll
  module Utils
    class << self
      alias_method :has_yaml_header_without_markdown?, :has_yaml_header?

      def has_yaml_header?(file)
        File.extname(file) == ".md" || has_yaml_header_without_markdown?(file)
      end
    end
  end
end

# Serve each page at the url wikic compiled its links to: /Alpha/beta/ for
# Alpha/beta.md and /Alpha/ for Alpha/index.md.
Jekyll::Hooks.register :pages, :post_init do |page|
  next unless page.path.end_with?(".md")

  base = page.path.sub(/\.md\z/, "").sub(%r{(\A|/)index\z}, "")
  page.data["permalink"] ||= base.empty? ? "/" : "/#{base}/"
end

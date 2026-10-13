# Serve raw .md sources alongside rendered HTML pages.
# /Slides/foo/index.md is copied to _site as-is, and also as /Slides/foo.md
Jekyll::Hooks.register :site, :post_write do |site|
  site.pages.each do |page|
    next unless page.path.end_with?('.md')

    src = File.join(site.source, page.path)
    next unless File.exist?(src)

    dest = File.join(site.dest, page.path)
    FileUtils.mkdir_p(File.dirname(dest))
    FileUtils.cp(src, dest)

    if File.basename(page.path) == 'index.md' && File.dirname(page.path) != '.'
      FileUtils.cp(src, File.join(site.dest, "#{File.dirname(page.path)}.md"))
    end
  end
end

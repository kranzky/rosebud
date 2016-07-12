#!/usr/bin/env ruby

require 'byebug'
require 'awesome_print'

require 'capybara'
require 'capybara/dsl'
require 'capybara/poltergeist'

require 'phrasie'
require 'cld'

class Rosebud
  include Capybara::DSL

  def initialize
    options = { js_errors: false }
    Capybara.register_driver :poltergeist do |app|
      Capybara::Poltergeist::Driver.new(app, options)
    end
    Capybara.default_driver = :poltergeist
    Capybara.current_session.driver.add_headers('User-Agent' => _iPhone[:user_agent])
    Capybara.current_session.driver.resize_window(*_iPhone[:dimensions])
  end

  def exercise
    Dir["*.json"].each do |name|
      contents = JSON.parse(File.read(name))
      _extract(contents)
    end
  end

  def process(url)
    contents = _retrieve(url)
    File.open(name, "w") { |file| file.write(contents.to_json) }
    _extract(contents)
  end

  private

  def _retrieve(url)
    visit url
    {
      url: page.current_url,
      title: page.title,
      status: page.status_code,
      html: page.html,
      image: page.save_screenshot
    }
  end

  def _extract(data)
    doc = Nokogiri::HTML(data["html"])
    head = _extract_head(doc)
    url = _extract_url(data["url"], head)
    title = _extract_title(data["title"], head, doc)
    body = _extract_body(title, doc)
    summary = _extract_summary(head, body)
    text = _extract_text(body)
    language = _extract_language(head, text)
    keywords = _extract_keywords(head, text)
    {
      url: url,
      title: title,
      summary: summary,
      provider: {
        name: "",
        url: "",
        icon: ""
      },
      authors: [{
        name: "",
        url: "",
        icon: ""
      }],
      published: "",
      language: language,
      keywords: keywords,
      images: [],
      banner: "",
      screenshot: data["image"],
      html: "",
      text: ""
    }
  end

  def _extract_head(doc)
    retval = { meta: [], link: [] }
    doc.css("meta").each do |data|
      values = data.attributes.values
      retval[:meta] << Hash[values.map { |a| [a.name.to_sym, a.value] }]
    end
    link = []
    doc.css("link").each do |data|
      next if data['rel'] == 'stylesheet'
      values = data.attributes.values
      retval[:link] << Hash[values.map { |a| [a.name.to_sym, a.value] }]
    end
    retval[:oembed] = _extract_oembed(retval[:link])
    retval[:ograph] = _extract_meta(retval[:meta], /\Aog:/)
    retval[:article] = _extract_meta(retval[:meta], /\Aarticle:/)
    retval[:twitter] = _extract_meta(retval[:meta], /\Atwitter:/)
    # do music, video, book, profile
    links = retval[:link].select { |link| link[:type].nil? && !link[:rel].nil? }
    retval[:link] = Hash[links.map { |link| [link[:rel].gsub(/[-: ]/, '_').to_sym, link[:href]] }]
    meta = retval[:meta].select { |meta| !(meta[:name] || meta[:property]).nil? }
    retval[:meta] = Hash[meta.map { |meta| [(meta[:name] || meta[:property]).gsub(/[-: ]/, '_').to_sym, meta[:content]] }]
    retval
  end

  def _extract_oembed(links)
    link = links.find { |link| link[:type] == 'application/json+oembed' }
    return {} if link.nil?
    url = link[:href]
    Hash[JSON.parse(Net::HTTP.get(URI(url))).map do |k, v|
      [k.to_sym, v]
    end]
  end

  def _extract_meta(meta, pattern)
    tags = meta.select { |tag| tag[:name] =~ pattern || tag[:property] =~ pattern }
    meta.reject! { |tag| tags.include?(tag) }
    Hash[tags.map do |tag|
      name = (tag[:name] || tag[:property]).gsub(pattern, '')
      name.gsub!(':', '_')
      [name.to_sym, tag[:content]]
    end]
  end

  # we could use twitter or ograph here...
  def _extract_url(fallback, head)
    head[:link][:canonical] || fallback
  end

  # build a list of candidate titles
  # look at page elements that might contain the title
  # ultimately find the correct title string
  def _extract_title(fallback, head, doc)
    candidates = [fallback]
    header = doc.css('h1').map(&:text)
    header = doc.css('h2').map(&:text) if header.first.nil?
    header = doc.css('h3').map(&:text) if header.first.nil?
    header = doc.css('h4').map(&:text) if header.first.nil?
    header = doc.css('h5').map(&:text) if header.first.nil?
    header = doc.css('h6').map(&:text) if header.first.nil?
    candidates << head[:twitter][:title]
    candidates << head[:ograph][:title]
    candidates |= header
    candidates.compact!
    candidates.map!(&:strip)
    ap candidates
    fallback
  end

  def _extract_body(title, doc)
    #doc.css("body").first.search("[text()*='#{title}']").first.parent
    doc
  end

  # use description meta tag
  def _extract_summary(head, doc)
    "whatever"
  end

  def _extract_text(body)
    body.text
  end

  # use language meta tag
  def _extract_language(head, text)
    CLD.detect_language(text)[:code]
  end

  # use keywords meta tag
  def _extract_keywords(head, text)
    extractor = Phrasie::Extractor.new
    auto =
      extractor
        .phrases(text)
        .map(&:first)
        .map(&:downcase)
        .reject { |k| k !~ /\A[\p{Alnum}]+\Z/ }
    keywords = auto[0...10].sort.uniq
  end

  def _iPhone
    {
      dimensions: [736, 414],
      user_agent: "Mozilla/5.0 (iPhone; CPU iPhone OS 9_1 like Mac OS X) AppleWebKit/601.1.46 (KHTML, like Gecko) Version/9.0 Mobile/13B143 Safari/601.1"
    }
  end
end

Rosebud.new.exercise

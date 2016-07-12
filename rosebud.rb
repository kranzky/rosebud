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
    Capybara.default_driver = :poltergeist
    Capybara.current_session.driver.add_headers('User-Agent' => _iPhone[:user_agent])
    Capybara.current_session.driver.resize_window(*_iPhone[:dimensions])
  end

  def process(url)
#   contents = _retrieve(url)
#   File.open("results.json", "w") { |file| file.write(contents.to_json) }
    contents = JSON.parse(File.read("results.json"))
    _extract(contents)
  end

  private

  def _retrieve(url)
    visit url
    _wait_for_page_load
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
    url = _extract_url(data["url"], head),
    title = _extract_title(data["title"], head, doc)
    body = _extract_body(title, doc)
    text = _extract_text(body)
    language = _extract_language(head, text)
    keywords = _extract_keywords(head, text)
    {
      url: url,
      title: title,
      summary: "",
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
    doc.css("meta").select do |data|
      values = data.attributes.values
      retval[:meta] << Hash[values.map { |a| [a.name.to_sym, a.value] }]
    end
    link = []
    doc.css("link").select do |data|
      values = data.attributes.values
      retval[:link] << Hash[values.map { |a| [a.name.to_sym, a.value] }]
    end
    retval
  end

  def _extract_url(fallback, head)
    fallback
  end

  def _extract_title(fallback, head, doc)
    "Homeopathy: the air guitar of medicine"
  end

  def _extract_body(title, doc)
    doc.css("body").first.search("[text()*='#{title}']").first.parent
  end

  def _extract_text(body)
    body.text
  end

  def _extract_language(head, text)
    CLD.detect_language(text)[:code]
  end

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

  def _wait_for_page_load
    Timeout.timeout(Capybara.default_max_wait_time) do
      loop until page.evaluate_script('jQuery.active').zero?
    end
  end

  def _iPhone
    {
      dimensions: [736, 414],
      user_agent: "Mozilla/5.0 (iPhone; CPU iPhone OS 9_1 like Mac OS X) AppleWebKit/601.1.46 (KHTML, like Gecko) Version/9.0 Mobile/13B143 Safari/601.1"
    }
  end
end

ap Rosebud.new.process(ARGV.first)

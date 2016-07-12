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
#   contents = _extract(url)
#   File.open("results.json", "w") { |file| file.write(contents.to_json) }
    contents = JSON.parse(File.read("results.json"))
    _convert(contents)
  end

  private

  def _extract(url)
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

  def _convert(data)
    doc = Nokogiri::HTML(data["html"])
    meta = []
    doc.css("meta").select do |data|
      values = data.attributes.values
      meta << Hash[values.map { |a| [a.name, a.value] }]
    end
    link = []
    doc.css("link").select do |data|
      values = data.attributes.values
      link << Hash[values.map { |a| [a.name, a.value] }]
    end
    body = doc.css("body").first
    text = body.text
    language = CLD.detect_language(text)[:code]
    # TODO: use the open graph protocol for title, type, url, image etc
    # TODO: there's also the twitter card and oembed data (via URL)
    # TODO: use the "original-source" or "canonical" or "shortlink" link rel
    url = data["url"]
    # TODO: use the "news_keywords" meta
    keywords = Phrasie::Extractor.new.phrases(text)[0...10].map(&:first)
    {
      url: url,
      title: "",
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

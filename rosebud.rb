#!/usr/bin/env ruby

require 'byebug'
require 'awesome_print'

require 'capybara'
require 'capybara/dsl'
require 'capybara/poltergeist'

class Rosebud
  include Capybara::DSL

  def initialize
    Capybara.default_driver = :poltergeist
    Capybara.current_session.driver.add_headers('User-Agent' => _iPhone[:user_agent])
    Capybara.current_session.driver.resize_window(*_iPhone[:dimensions])
  end

  def scrape(url)
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

  private

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

results = Rosebud.new.scrape(ARGV.first)
debugger

ap results

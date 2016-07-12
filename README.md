ROSEBUD
=======

Extract web page content.

TODO
----

* Extract
  + canonical URL (after redirects)
  + canonical body
    - images with captions
  + language (use that google library)
  + tag extraction
  + screenshot
  + title
  + description (first para or embed)
  + thumbnail (maybe from embed)
  + list of body images
  + media
  + author(s)
    - name
    - url
    - avatar
  + source
    - name
    - url
    - favicon
  + publication date
* Implement
  + Load page and save (http://ngauthier.com/2014/06/scraping-the-web-with-ruby.html)
    - phantomjs / selenium
    - Canonical URL
    - HTML
    - Screenshot
  + Then write Journalist
    - Take HTML and extract pertinent stuff
    - Reformat into some canonical form (headings, paragraphs, images, captions)

Copyright
---------

Copyright (c) 2016 Jason Hutchens. See UNLICENSE for further details.

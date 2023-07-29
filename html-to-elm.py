import sublime
import sublime_plugin

from html.parser import HTMLParser
import re

class HtmlToElmParser(HTMLParser):
  def __init__(self, indent_size = 4):
    super().__init__()
    self.result = ""

    self.depth = -1
    self.context = {}
    self.INDENT_SIZE = indent_size

  def indentation(self, depth):
    return " " * (self.INDENT_SIZE * depth)

  
  def trim(self, str):
    return re.sub("^[\n\t ]+|[\n\t ]+$/g", "", str)
  
  def map_attr(self, attr):
    # handle elm type keyword 
    style_attrs = []

    if attr[0] == "type":
      attr = ("type_", attr[1])
    elif attr[0] == "class":
      attr = ("class_", attr[1])
    elif attr[0] == "style":       
      xs = attr[1].split(";")
      for s in xs:
        sp = s.split(':')
        if len(sp) == 2:
          style_attrs.append("style \"%s\" \"%s\"" % (sp[0].strip(), sp[1].strip()))

    if len(style_attrs) > 0:
      return ", ".join(style_attrs)

    # handle data-<CUSTOM> attrs, TODO: check list of build in elm functions, if not present, use attribute fn to deal with
    if (attr[0].find("data-") >= 0) or (attr[0].find("role") >= 0):
      return "attribute \"" + attr[0] + "\" \"" + attr[1] + "\""

    return attr[0] + " \"" + attr[1] + "\""

  def handle_starttag(self, tag, attrs):
    pre = ""
    _tag = []

    self.depth += 1

    # Add a coma if there is already a tag at the same depth with the same
    # parent
    if (self.depth in self.context) and self.context[self.depth] == True:
      pre = "\n" + self.indentation(self.depth) + ","
    else:
      self.context[self.depth] = True

    # Add space before html tag
    pre += " " if self.depth else ""

    # get attrs
    _attrs = list(map(self.map_attr, attrs))

    # Add all element into the tag array
    _tag.append(pre + tag)
    _tag.append("\n" + self.indentation(self.depth + 1) + "[")

    if len(_attrs) > 0:
      _tag.append(" " + ", ".join(_attrs) + " ")

    _tag.append("]\n" + self.indentation(self.depth + 1) + "[")

    self.result += "".join(_tag)

  def handle_endtag(self, tag):
    if ((self.depth + 1) in self.context) and self.context[self.depth] == True:
      self.context[self.depth + 1] = False
      self.result += "\n" + self.indentation(self.depth + 1)
    self.depth -= 1
    self.result += "]"

  def handle_data(self, data):
    text = self.trim(data)
    if len(text) > 0:
      self.result += " text \"" + text + "\""
      

def convert_html(input):
  parser = HtmlToElmParser()
  parser.feed(input)
  return parser.result

class HtmlToElmCommand(sublime_plugin.TextCommand):
  def run(self, edit):
    for region in self.view.sel():
      if not region.empty(): 
        # Get the selected text  
        s = self.view.substr(region)  
        # s = s.replace("Hello", "Nazdar")
        # check if HTML?
        html = s
        # parse html
        elm = convert_html(html)
        # Replace the selection with transformed text  
        self.view.replace(edit, region, elm)  

'''
Moduling for parsing html
'''
import re

class BaseNavigableItem():

    ATTRIBUTE_REGEX = r'(?P<attribute_name>[\w"\'-]+)(' + \
                      r'\s*=\s*"(?P<val_opt1>[^"]*)"|' + \
                      r'\s*=\s*\'(?P<val_opt2>[^\']*)\'|' + \
                      r'\s*=\s*(?P<val_opt3>[^>\s]+)|' + \
                      r'(?=(\s|/>|>)))' # target: required

    ATTRIBUTE_PATTERN = re.compile(ATTRIBUTE_REGEX)

    # OC_TAG_PATTERN = OPENING_AND_CLOSING_TAG_PATTERN
    # Closing tag '>' is intentionally included in the 'attrs' capture group
    OC_TAG_REGEX = r'((?P<html_comment><\!\-\-.*?\-\->)|' + \
                   r'(?P<opening_tag>' + \
                   r'<\s*(?P<o_tag_name>\w[\w\d]*)(?P<attrs>' + \
                   r'(\s(\s*' + \
                   ATTRIBUTE_REGEX + \
                   r')*)?' + \
                   r'(?P<self_closing>\s*/\s*)?>))|' + \
                   r'(?P<closing_tag>' + \
                   r'</(?P<c_tag_name>\w+)>))'

    OC_TAG_PATTERN = re.compile(OC_TAG_REGEX, re.DOTALL)

    COMBINED_STRING_TAG_PATTERN = re.compile(r'(' + OC_TAG_REGEX + '|'
                                             r'(?P<plain_text>[^<]+))')

    ATTRIBUTE_VALUE_OPTIONS = ['val_opt1', 'val_opt2', 'val_opt3']

    HTML_SINGLETONS = ['area', 'base', 'br', 'col', 'command', 'embed', 'hr',
                       'img', 'input', 'keygen', 'link', 'meta', 'param',
                       'source', 'track', 'wbr']

    def __init__(self):
        self.child_tags = []
        self.parent = None
        self.attributes = {}
        self.inner_content = ''

    def find(self, tag_name, attribute_dict=None, recursive=True,
             exact_class=False, bfs=False, string=None, string_contains=None):
        '''
        Used to find the very first match
        '''
        matches = self.find_all(tag_name, attribute_dict, recursive,
                                exact_class, bfs, string, string_contains,
                                find_first=True)
        if matches:
            return matches[0]
        return None

    def find_all(self, tag_name, attribute_dict=None, recursive=True,
                 exact_class=False, bfs=False, string=None,
                 string_contains=None, find_first=False):
        '''
        Used to find all tags in within a node that matches ....
        '''
        if attribute_dict:
            assert isinstance(attribute_dict, dict), f"Expected "\
                                        f"attribute_dict to be of type " \
                                        f"'dict' but got " \
                                        f"{type(attribute_dict)} instead"
        else:
            attribute_dict = {}
        matches = []
        child_tags = self.child_tags
        while child_tags:
            next_child_tags = []
            for child_tag in child_tags:
                if child_tag.tag_name == tag_name.lower():
                    match = True
                    if not child_tag._compare_attributes(attribute_dict,
                                                         exact_class):
                        match = False

                    if string and not child_tag._compare_strings(string):
                        match = False

                    elif string_contains and not child_tag \
                                ._compare_strings(string_contains= \
                                                  string_contains):
                        match = False

                    if match:
                        matches.append(child_tag)
                        if find_first:
                            return matches

                if matches and find_first:
                    return matches

                if recursive and not bfs:
                    matches.extend(child_tag.find_all(tag_name, attribute_dict,
                                                      recursive, exact_class,
                                                      bfs, string,
                                                      string_contains,
                                                      find_first))
                    if matches and find_first:
                        return matches

                if recursive and bfs:
                    next_child_tags.extend(child_tag.child_tags)
            child_tags = next_child_tags
        return matches


    def _compare_attributes(self, attribute_dict, exact_class=False):
        '''
        Method for comparing attributes of self and an attribute dictionary
        '''
        for key, value in attribute_dict.items():
            try:
                # Special case for handling class comparisons
                if key == "class":
                    if isinstance(value, str):
                        class_set = set([val.lower() \
                                         for val in value.split(" ")])
                    elif isinstance(value, list):
                        class_set = set([val.lower() for val in \
                                         value])
                    else:
                        raise TypeError(f"Expected 'class' key in " \
                                        f"attribute_dict to be either of " \
                                        f"type 'list' or 'String' but got" \
                                        f"{type(attribute_dict)} instead.")
                    if exact_class:
                        assert class_set == set(self['class'])
                    else:
                        assert class_set.issubset(set(self['class']))
                # General attribute handling comparisons
                else:
                    assert self[key] == value
            except (AssertionError, KeyError):
                return False
        return True

    @property
    def string(self):
        match = self.COMBINED_STRING_TAG_PATTERN.finditer(self.inner_content)
        text = ''
        for match in match:
            if match.group('plain_text'):
                text += match.group('plain_text')
        return text

    def _compare_strings(self, string=None, string_contains=None):
        if string_contains:
            return string_contains in self.string
        return string == self.string

    def __getattr__(self, item):
        if "__" in item:
            tag, xpath_index = tuple(item.split('__'))
            try:
                return self.find_all(tag, recursive=False, \
                                     bfs=True)[int(xpath_index)-1]
            except IndexError:
                raise IndexError(f'"{tag}" with xpath index {xpath_index} '
                                 f'was not found within "{self.tag_name}"')
            except TypeError:
                raise TypeError("Something unexpected is happening")
        match = self.find(item, bfs=True)
        if match:
            return match
        else:
            raise AttributeError(f"Failed to find any '{item}' tag within "
                                 f"'{self.tag_name}' tag.")


class LittleString(str):
    def __new__(cls, string, parent_tag):
        obj = string.__new__(cls, string)
        return obj

    def __init__(self, string, parent_tag):
        self.parent = parent_tag


class LittleTag(BaseNavigableItem):
    '''
    Class to handle tag objects which will also be extended by LittleSoup
    class
    '''
    def __init__(self, o_re_tag_obj, parser):
        self.o_re_tag_obj = o_re_tag_obj
        self.tag_name = o_re_tag_obj.group('o_tag_name').lower()
        self.opening_tag = o_re_tag_obj.group(0)
        self.parser = parser
        self.closing_tag = None
        self._closed = False
        self.c_re_tag_obj = None
        self.inner_content = ''
        self.attribute_dict = {}
        self.child_tags = []
        self.parent = None
        self._extract_attributes()

    def _close(self, c_re_tag_obj=None, forced_close=False, raw_position=None):
        if not self._closed:
            _, inner_content_start = self.o_re_tag_obj.span()
            if c_re_tag_obj:
                inner_content_end, _ = c_re_tag_obj.span()
            elif raw_position:
                inner_content_end = raw_position
            else:
                raise AssertionError("Expected either parameter 'c_re_tag_obj'"
                                     "or 'raw_position' but got None")
            self.inner_content = self.parser \
                                     .raw_html[inner_content_start: \
                                               inner_content_end]
            self._closed = True
            if forced_close:
                self.parser.unbalanced_tags = True
            else:
                self.c_re_tag_obj = c_re_tag_obj
                self.closing_tag = self.c_re_tag_obj.group(0)

    def add_child(self, child_tag):
        '''
        Used to add a child to a tag
        '''
        self.child_tags.append(child_tag)
        child_tag.parent = self

    @property
    def has_child(self):
        '''
        Quickly check if an object has children
        '''
        return bool(self.child_tags)

    @property
    def string(self):
        text = super().string
        return LittleString(text, parent_tag=self)

    @property
    def attrs(self):
        '''
        Short-hand to get attributes dictionary
        '''
        return self.attribute_dict

    def _pass_children_to(self, parent_tag):
        # Do not use add_child method since that will make this tag_object
        # the parent, which is not what we want.
        parent_tag.child_tags.extend(self.child_tags)

    def _extract_attributes(self):
        attributes_string = self.o_re_tag_obj.group('attrs').replace("\n", " ")
        attributes_string = attributes_string.replace("\r", " ")
        attributes = self.ATTRIBUTE_PATTERN.finditer(attributes_string)
        for attribute in attributes:
            attribute_name = attribute.group("attribute_name").lower()
            attribute_value = None
            for value_option in self.ATTRIBUTE_VALUE_OPTIONS:
                if attribute.group(value_option) is not None:
                    attribute_value = attribute.group(value_option)
                    if attribute_name == "class":
                        attribute_value = attribute_value.strip("'").strip('"')
                        attribute_value = attribute_value.lower().split(" ")
                    break
            self.attribute_dict[attribute_name] = attribute_value

    def __getitem__(self, key):
        # Consider raising error
        assert isinstance(key, str), f"Expected subscribtable key to be of " \
                                     f"type string but got {type(key)} " \
                                     f"instead"
        try:
            return self.attribute_dict[key]
        except KeyError:
            raise KeyError(f" '{key}'")

    def __eq__(self, other):
        if self.tag_name == other.tag_name.lower():
            return self._compare_attributes(other.attrs, exact_class=True)
        return True

    def __str__(self):
        if self.tag_name in self.HTML_SINGLETONS:
            return str(self.opening_tag)
        else:
            if self.closing_tag:
                return str(self.opening_tag) + self.inner_content + \
                                               str(self.closing_tag)
            return self.opening_tag + self.inner_content

    def __repr__(self):
        return self.opening_tag


class LittleSoup(BaseNavigableItem):
    '''
    Class for parsing HTML
    '''
    def __init__(self, raw_html, encoding=None):
        self.raw_html = self._process_html(raw_html, encoding)
        self.root_tags = []
        self.child_tags = self.root_tags
        self.parent = None
        self.inner_content = ''
        self.attribute_dict = {}
        self.tag_name = 'main_soup'
        self.unbalanced_tags = False
        self._parse_tags()

    def _parse_tags(self):
        '''
        Method to extract both opening and closing tags, in their order, from
        the raw html
        '''
        re_tag_objs = list(self.OC_TAG_PATTERN.finditer(self.raw_html))
        opened_tags = []

        # Build tag tree here
        for re_tag_obj in re_tag_objs:
            # This block deals with an instance of an opening tag
            if re_tag_obj.group('opening_tag'):
                o_little_tag = LittleTag(re_tag_obj, parser=self)
                if o_little_tag.tag_name.lower() in self.HTML_SINGLETONS or \
                    re_tag_obj.group('self_closing'):
                    if opened_tags:
                        opened_tags[-1].add_child(o_little_tag)
                    else:
                        self.root_tags.append(o_little_tag)
                else:
                    opened_tags.append(o_little_tag)

            # This block deals with an instance of a closing tag
            elif re_tag_obj.group('closing_tag'):
                # Began to change things
                i = -1 # Start from the back
                negative_len = -len(opened_tags) - 1
                try:
                    last_tag = opened_tags[-1]
                except IndexError:
                    # Just pass. If there is no last_tag then the while loop
                    # below won't run cause i will be less than 0
                    last_tag = None
                while i > negative_len:
                    o_little_tag = opened_tags[i]
                    if o_little_tag.tag_name == re_tag_obj \
                                                .group('c_tag_name').lower():
                        # Close here before checking if o_little_tag is last
                        # tag. This will prevent mistakenly force closing
                        # o_little_tag
                        o_little_tag._close(re_tag_obj)

                        if o_little_tag is not last_tag:
                            o_little_tag = \
                                self._recursively_force_close(opened_tags[i:],
                                                              re_tag_obj)

                        try:
                            parent_tag = opened_tags[i-1]
                            parent_tag.add_child(o_little_tag)
                        except IndexError:
                            self.root_tags.append(o_little_tag)
                        opened_tags = opened_tags[:i]
                        break
                    i -= 1

        # If there are some things still left, recursively close them and add
        # them to the root tag
        if opened_tags:
            end = len(self.raw_html)
            root_tag = self._recursively_force_close(opened_tags,
                                                     raw_position=end)
            root_tag._close(forced_close=True, raw_position=end)
            self.root_tags.append(root_tag)

    @property
    def string(self):
        text = super().string()
        return LittleString(text, self)

    def _process_html(self, content, encoding):
        if isinstance(content, str):
            # Any further processing to string can be done here
            return content
        elif isinstance(content, bytes):
            assert encoding, f"Bytes object was passed to class " \
                             f"without adding parameter for encoding."
            content = content.decode(encoding)
            return content
        else:
            raise TypeError(f"Expected parameter 'content' to be either of " \
                            f"type 'Bytes' or 'String' but got " \
                            f"{type(content)} instead.")

    def _recursively_force_close(self, unclosed_tags, c_re_tag_obj=None,
                                 raw_position=None):
        '''
        Method force closes all but the first element
        '''
        for j in range(-1, -len(unclosed_tags), -1):
            if c_re_tag_obj:
                unclosed_tags[j]._close(c_re_tag_obj=c_re_tag_obj,
                                        forced_close=True)
            elif raw_position:
                unclosed_tags[j]._close(raw_position=raw_position,
                                        forced_close=True)
            else:
                raise AssertionError("Expected either parameter 'c_re_tag_obj'"
                                     "or 'raw_position' but got None")
            unclosed_tags[j-1].add_child(unclosed_tags[j])
        return unclosed_tags[0]

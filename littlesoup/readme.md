This file will indicate some differences between LittleSoup and
BeautifulSoup in terms of their usage.

## Importing
```
>>> from bs4 import BeautifulSoup
>>> from littlesoup import LittleSoup

```
## Creating a soup from a string of HTML content
Beautifulsoup requires you to specify the parser you want to use. LittleSoup
on the other hand, uses just one parser, hence does not require any
other parameter except your string.

```
>>> htmlcontent = '<html>.........................</html>'
>>> bsoup = BeautifulSoup(htmlcontent, 'html.parser')
>>> lsoup = LittleSoup(htmlcontent)

```

## Creating a soup from bytes content or requests library response
Normally, you will be working with libraries such as requests library, to
get pages, and parse them using your html parser. These libraries get
information in bytes. LittleSoup does not have methods for guessing the
encoding of byte content. However, libraries such as the requests library
do that for us, so we just have to pass in the encoding as an extra
parameter.

```
>>> response = requests.get(some_url)
>>> bsoup = BeautifulSoup(response.content, 'html.parser')
>>> lsoup = LittleSoup(response.content, response.encoding)

```

## Navigating a soup using attributes
Naturally, you can navigate a soup in bs4 using the '.' method like so:

```
>>> bsoup.body.div.p

```
This finds the first div in the whole file (from top-to-down) and finds the
next p inside the div. This (top-to-down) method is actually implemented
using something similar to a depth-first search.

You can interact with littlesoup in the same way:

```
>>> lsoup.body.div.p

```
The difference is that littlesoup uses breadth-first search. Which means it
tries to first direct child of body that is a div, and goes on to find the
first grand-child of body that is a div, and so on until it finds one. This
behaviour is intentional as it allows us to provide an API for xpaths, which
we will see in the next section.


## API for Xpaths
littlesoup provides a nice API for xpaths, which can be used to navigate a
DOM for a particular file. To travel down this xpath:
html/body/div[3]/div/div[4]/ul[1]/li[4]/b
You would do so:

```
>>> lsoup.body.div__3.div.div__4.ul__1.li__4.b

```
Note that it uses a double underscore to separate the name of a tag from it's
xpath index


## Finding Elements
```
>>> lsoup.find('a')
>>> lsoup.find_all('a')

```
Naturally, the find and find_all methods implement the depth-first searching
used in bs4. Which means it finds the first element from top-down and then
the next after that.
If you want to use a breadth-first search, such that elements closest to the
top, in terms of heirarchy, are found first, you use:

```
>>> lsoup.body.div.find('a', bfs=True)

```
If you want to specify attributes you can use:

```
>>> lsoup.find('a', {'href': 'https://www.somesite.com'})

```
If you want to specify the string inside a tag, you use the string parameter:

```
>>> lsoup.find('a', {'href': 'https://www.somesite.com'}, string='Click Here')

```
If you want to specify a part of the string inside a tag, you use
string_contains parameter:

```
>>> lsoup.body.find('a', string_contains='Click')

```
Class attributes are treated a bit differently. You can search all objects
belonging to a specific class like so:

```
>>> lsoup.find('a', {'class': 'header'})

```
Naturally, this will return all elements belonging to that class including:
<a class="header logo"></a> If you want to avoid this and have an exact class
match you use:

```
>>> lsoup.find('a', {'class': 'header'}, exact_class=True)

```
You can specify multiple classes as space-separated values or a list of
classes like this:

```
>>> lsoup.find('a', {'class': 'header clickable-item special-red'})

```
or:

```
>>> lsoup.find('a', {'class': ['header', 'clickable-item', 'special-red']})

```
Again, any items containing all of these classes will be returned, and you
can get exact matches with exact_class.

You can get the parent of any tag with the parent attribute and the text it
contains with the text attribute

```
>>> div = lsoup.find('div', {'class': 'list-item', 'href': 'some_link'})
>>> parent = div.parent
>>> string = div.string

```
You can also get all the children it contains with child_tags attribute:

```
>>> lsoup.div.child_tags

```
If you want to search just the children of an element, you can set the
recursive parameter to False

```
>>> lsoup.body.find('div', {'class': 'header'}, recursive=False)

```
Lastly, strings returned from the '.string' method of a tag are navigable.
This means you can access their parents

``` >>> string = lsoup.body.div.div__3.string
>>> div__3 = string.parent
```

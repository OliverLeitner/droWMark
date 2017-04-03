import sys
import os
from wordpress_xmlrpc import Client, WordPressPost, WordPressPage
from wordpress_xmlrpc.methods.posts import NewPost, EditPost, DeletePost, GetPost, GetPosts
from wordpress_xmlrpc.compat import xmlrpc_client
from wordpress_xmlrpc.methods import media, posts

try:
    from configparser import ConfigParser
except ImportError:
    from ConfigParser import ConfigParser
from io import StringIO
import codecs
import panflute as pf
from os import path
import mimetypes

WP = None
postfile = ''
script_dir = os.path.dirname(os.path.realpath(__file__))
home = os.path.expanduser('~')

def getConfig():
    """
    read configuration and return a set wordpress link
    """
    config = ConfigParser()
    config.read(home + '/.vimblogrc')

    url = config.get('blog0','url')
    url = 'https://' + url + '/xmlrpc.php'
    username = config.get('blog0','username')
    password = config.get('blog0','password')

    WP = Client( url, username, password )
    return WP


def imageURLs(elem, doc):
    """
    Panflute filter for Image URLs.
    Checks if the URLs are relative paths and match an image file. If they do,
    it uploads the image and changes the URL to point to that.
    """

    if isinstance(elem, pf.Image):
        # Handles paths if they are relative to the post
        here = path.dirname( postfile )
        url  = path.join( here, elem.url ) # Make path absolute
        mime = checkImage(url)
        res  = uploadFile(url, mime)
        elem.url = res['url']
        return elem

def codeBlocks(elem, doc):
    """
    If input is a CodeBlock, just tag it as a code piece and put the language.
    WordPress can handle the highlighting
    """
    if isinstance(elem, pf.CodeBlock):
        content  = elem.text
        language = None
        if len(elem.classes) >= 1:
            language = elem.classes[0]

        block = '[code'
        if language:
            block += ' language="%s"' % (language)
        block += ']\n%s\n[/code]' % (content)

        return pf.RawBlock(block)

def checkImage(url):
    """
    Checks if image path exists and if it's an image.
    @returns mime MIME type of the image or `None` if it's not an image.
    """
    if not path.exists(url):
        return
    mime = mimetypes.guess_type(url, strict = True)[0]
    if not mime.split('/')[0] == 'image':
        # It's not an image!
        return
    return mime

def uploadFile( url, mime ):
    """
    Uploads files to Wordpress
    @returns response {
      'id': 6,
      'file': 'picture.jpg'
      'url': 'http://www.example.com/wp-content/uploads/2012/04/16/picture.jpg',
      'type': 'image/jpeg',
    }
    """
    data = {}
    data['name'] = path.basename(url)
    data['type'] = mime
    with open(url) as f:
        data['bits'] = xmlrpc_client.Binary(f.read())

    response = WP.call(media.UploadFile(data))
    return response

def getAllPosts( offset, increment ):
    """
    lets do the wordpress post listing thing
    """

    WP = getConfig()

    print '============== blog entries ================='
    while True:
        posts = WP.call(GetPosts({'number': increment, 'offset': offset}))
        if len(posts) == 0:
            break  # no more posts returned
        for post in posts:
            #post_str = str(post)
            #tags = ','.join(map(str,post.terms))
            categories = ','.join(map(str,post.terms))
            print post.id + ' - ' + post.title + ' - ' + categories
        offset = offset + increment

def deletePost ( postid ):
    """
    delete a blogpost
    """
    WP = getConfig()
    post = WP.call(DeletePost(postid))
    print post

def publishPost ( postid ):
    """
    publish an existing post
    """
    WP = getConfig()
    post = WP.call(EditPost(postid, content))
    print post

def editPost ( postid ):
    """
    edit an existing post
    """
    # loading the template file for putting
    # returned markdown into
    postfile = script_dir + '/../templates/drowmark.template'
    file = open(postfile,'rU')
    buf = file.read()

    # getting the data of the post
    WP = getConfig()
    post = WP.call(GetPost(postid))

    #list of categories
    categories = config.get('blog0','categories')
    active_categories = '';
    for term in post.terms:
        if term.name in categories:
            active_categories += term.name + ','

    active_categories = active_categories[:-1]

    #active tags
    tags = ','.join(map(str,post.terms))

    # Take HTML, convert to markdown and put it as post content
    # Makes intermediate convertion to Panflute AST to apply the filters.
    postdocument = pf.convert_text(post.content, input_format='html',
                                                output_format='panflute',
                                                standalone=True)

    pf.run_filters( [ imageURLs, codeBlocks ], doc = postdocument )
    content = pf.convert_text(postdocument, input_format='panflute',
                                            output_format='markdown')

    #fill the template
    buf = buf.replace('{TITLE}',post.title)
    buf = buf.replace('{STATUS}',post.post_status)
    buf = buf.replace('{CATEGORIES}',active_categories)
    buf = buf.replace('{TAGS}',tags)
    buf = buf.replace('{CONTENT}',content)

    print buf
    sys.exit()

if __name__ == '__main__':

    # Get arguments from sys.argv, the idea is to
    # maintain it simple, making the python file
    # callable from outside VIM also.

    if not len(sys.argv) == 2:
         print('1 parameter needed:\n\t file')
         raise BaseException

    postfile = sys.argv[1]


    # Files are Markdown + INI mixed, INI is put
    # on the top of the file just for adding some
    # metadata, the separator is an horizontal ruler

    postconfig = ''
    postcontent = ''

    inheader = True
    f = codecs.open(postfile, 'r', 'utf-8')
    for line in f:
        if inheader:
            # FIXME Improve this check
            if line.strip() == '---':
                inheader = False
                continue
            postconfig += line
            continue
        if not inheader:
            postcontent += line
            continue
    f.close()

    # Parse the INI part
    buf = StringIO(postconfig)
    config_global = ConfigParser()
    config.readfp(buf)

    terms_names = {}
    tags = config.get('wordpress', 'tags')
    terms_names['post_tag'] = map(lambda x: x.strip(),tags.split(','))

    categories = config.get('wordpress', 'categories')
    terms_names['category'] = map(lambda x: x.strip(),categories.split(','))

    post_status = config.get('wordpress','status')

    title = config.get('wordpress','title')

    entrytype = config.get('wordpress','type')

    thumb_url = None
    if config.has_option('wordpress','thumbnail'):
        thumbnail = config.get('wordpress', 'thumbnail')
        here = path.dirname( postfile )
        thumb_url = path.join( here, thumbnail ) # Make path absolute

    # Wordpress related, create the post
    WP = getConfig()

    if entrytype != 'page':
        post = WordPressPost()
    else:
        page = WordPressPage()


    # Take markdown, convert to HTML and put it as post content
    # Makes intermediate convertion to Panflute AST to apply the filters.
    postdocument = pf.convert_text(postcontent, input_format='markdown',
                                                output_format='panflute',
                                                standalone=True)

    pf.run_filters( [ imageURLs, codeBlocks ], doc = postdocument )
    content = pf.convert_text(postdocument, input_format='panflute',
                                            output_format='html')

    if entrytype != 'page':
        # Set post metadata
        post.title = title
        post.content = content
        post.post_status = post_status
        post.terms_names = terms_names
    else:
        # i just do the same for pages
        # except we dont need the tags
        page.title = title
        page.content = content
        page.post_status = post_status

    if not thumb_url == None:
        thumb_mime = checkImage(thumb_url)
        if not thumb_mime == None:
            response = uploadFile(thumb_url, thumb_mime)
            if entrytype != 'page':
                post.thumbnail = response['id']
            else:
                page.thumbnail = response['id']

    if entrytype != 'page':
        post.id = WP.call(NewPost(post)) # Post it!
    else:
        page.id = WP.call(NewPost(page)) # or maybe post a page!
        post = page

    print( "Posted: " + post.title )
    print( "\nWith Status: " + post.post_status )
    print( "\nAnd ID: " + post.id )

import sys
import os
import glob
import tempfile
import pprint
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
username = ''
password = ''
url = ''
categories = ''
article_status = ''

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
    article_status = config.get('blog0','article_status')
    categories = config.get('blog0','categories')

    WP = Client( url, username, password )
    return WP

def getPostConfig( postfile ):
    """
    putting this into a separate function might help later on
    with cleanup.
    """
    post = WordPressPost()
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
    config = ConfigParser()
    config.readfp(buf)

    post.terms_names = {}
    post.tags = config.get('wordpress', 'tags')
    post.terms_names['post_tag'] = map(lambda x: x.strip(),post.tags.split(','))

    post.categories = config.get('wordpress', 'categories')
    post.terms_names['category'] = map(lambda x: x.strip(),post.categories.split(','))

    post.post_status = config.get('wordpress','status')

    post.title = config.get('wordpress','title')

    post.entrytype = config.get('wordpress','type')

    post.id = config.get('wordpress','id')

    post.content = postcontent

    post.thumb_url = None
    if config.has_option('wordpress','thumbnail'):
        post.thumbnail = config.get('wordpress', 'thumbnail')
        here = path.dirname( postfile )
        post.thumb_url = path.join( here, post.thumbnail ) # Make path absolute
    return post

def convertContent( inputcontent, source, target ):
    """
    content converter
    """
    postdocument = pf.convert_text(inputcontent, input_format=source,
                                                output_format='panflute',
                                                standalone=True)

    pf.run_filters( [ imageURLs, codeBlocks ], doc = postdocument )
    content = pf.convert_text(postdocument, input_format='panflute',
                                            output_format=target)
    return content

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
    content.post_status = article_status
    post = WP.call(EditPost(postid, content))
    print post

def updatePost ( updatepostfile ):
    """
    writeing back the changed content to db
    """
    WP = getConfig()
    post = getPostConfig(updatepostfile)
    update = WP.call(EditPost(post.id,post))

    print post.id

def editPost ( postid ):
    """
    edit an existing post
    """
    # loading the template file for putting
    # returned markdown into
    postfile = script_dir + '/../templates/drowmark.template'
    pfile = codecs.open(postfile, 'r', 'utf-8')
    buf = pfile.read()

    config = ConfigParser()
    config.read(home + '/.vimblogrc')
    configcategories = config.get('blog0','categories')

    # getting the data of the post
    WP = getConfig()
    post = WP.call(GetPost(postid))
    active_tags = ''
    active_categories = ''
    for term in post.terms:
        if term.name in configcategories:
            active_categories += term.name + ','
        else:
            active_tags += term.name + ','

    active_tags = active_tags[:-1]
    active_categories = active_categories[:-1]
    #categories = ','.join(map(str,post.categories))

    #converting the content back to markdown
    content = convertContent(post.content,'html','markdown')

    #fill the template
    buf = buf.replace('{ID}',post.id)
    buf = buf.replace('{TITLE}',post.title)
    buf = buf.replace('{STATUS}',post.post_status)
    buf = buf.replace('{CATEGORIES}',active_categories)
    buf = buf.replace('{TAGS}',active_tags)
    buf = buf.replace('{CONTENT}',content)

    f = tempfile.NamedTemporaryFile(suffix=post.id,prefix='vwp_edit',delete=False)
    filename = f.name
    f.close()
    with codecs.open(filename, 'w+b', encoding='utf-8') as fh:
        fh.write(buf)
        fh.seek(0)

    print f.name

if __name__ == '__main__':

    # Get arguments from sys.argv, the idea is to
    # maintain it simple, making the python file
    # callable from outside VIM also.

    if not len(sys.argv) == 2:
         print('1 parameter needed:\n\t file')
         raise BaseException

    postfile = sys.argv[1]

    # grabbing the template and inserting what we already can...
    newpost = getPostConfig(postfile)

    # Wordpress related, create the post
    WP = getConfig()

    if newpost.entrytype != 'page':
        post = WordPressPost()
    else:
        page = WordPressPage()

    #converting the content back to markdown
    content = convertContent(newpost.content,'markdown','html')

    if newpost.entrytype != 'page':
        # Set post metadata
        post.title = newpost.title
        post.content = content
        post.post_status = newpost.post_status
        post.terms_names = newpost.terms_names
    else:
        # i just do the same for pages
        # except we dont need the tags
        page.title = newpost.title
        page.content = content
        page.post_status = newpost.post_status

    if not newpost.thumb_url == None:
        thumb_mime = checkImage(newpost.thumb_url)
        if not thumb_mime == None:
            response = uploadFile(newpost.thumb_url, thumb_mime)
            if newpost.entrytype != 'page':
                post.thumbnail = response['id']
            else:
                page.thumbnail = response['id']

    if newpost.entrytype != 'page':
        post.id = WP.call(NewPost(post)) # Post it!
    else:
        page.id = WP.call(NewPost(page)) # or maybe post a page!
        post = page

    print( "Posted: " + post.title )
    print( "\nWith Status: " + post.post_status )
    print( "\nAnd ID: " + post.id )

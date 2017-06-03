"""
wordpress handler
"""
from __future__ import print_function

import sys
import os
import tempfile
import codecs
import mimetypes

from io import StringIO
from configparser import ConfigParser

from wordpress_xmlrpc import Client, WordPressPost, WordPressPage
from wordpress_xmlrpc.methods.posts import NewPost, EditPost, DeletePost, GetPost, GetPosts
from wordpress_xmlrpc.compat import xmlrpc_client
from wordpress_xmlrpc.methods import media #, posts

import panflute as pf

CATEGORIES = ''
ARTICLE_STATUS = ''

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
HOME = os.path.expanduser('~')

def myremovefiles(path, pid):
    """
    just remove some files by wildcard
    """
    files = os.listdir(path)
    for fileentries in files:
        if fileentries.endswith(pid):
            os.remove(os.path.join(path, fileentries))

def mygetconfig():
    """
    read configuration and return a set wordpress link
    """
    config = ConfigParser()
    if os.name == 'posix':
        config.read(SCRIPT_DIR + '/../.vimblogrc')
    else:
        #this should cover windows
        config.read(SCRIPT_DIR + '/../_vimblogrc')

    # FIXME remove any global deps
    global CATEGORIES, ARTICLE_STATUS
    url = config.get('blog0', 'url')
    url = 'https://' + url + '/xmlrpc.php'
    username = config.get('blog0', 'username')
    password = config.get('blog0', 'password')
    ARTICLE_STATUS = config.get('blog0', 'article_status')
    CATEGORIES = config.get('blog0', 'categories')

    my_link = Client(url, username, password)
    return my_link

def mygetpostconfig(s_postfile):
    """
    putting this into a separate function might help later on
    with cleanup.
    """
    l_post = WordPressPost()
    postconfig = ''
    postcontent = ''

    inheader = True
    tmp_file = codecs.open(s_postfile, 'r', 'utf-8')
    for line in tmp_file:
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
    tmp_file.close()

    # Parse the INI part
    buf = StringIO(postconfig)
    config = ConfigParser()
    config.readfp(buf)

    l_post.terms_names = {}
    l_post.tags = config.get('wordpress', 'tags')
    # FIXME clearing up unneeded map
    l_post.terms_names['post_tag'] = list(map(lambda x: x.strip(), l_post.tags.split(',')))
    l_post.categories = config.get('wordpress', 'categories')
    # FIXME clearing up unneeded map
    l_post.terms_names['category'] = list(map(lambda x: x.strip(), l_post.categories.split(',')))
    l_post.post_status = config.get('wordpress', 'status')
    l_post.title = config.get('wordpress', 'title')
    l_post.entrytype = config.get('wordpress', 'type')
    l_post.id = config.get('wordpress', 'id')
    l_post.content = postcontent
    l_post.thumb_url = None
    if config.has_option('wordpress', 'thumbnail'):
        l_post.thumbnail = config.get('wordpress', 'thumbnail')
        here = os.path.dirname(s_postfile)
        l_post.thumb_url = os.path.join(here, l_post.thumbnail) # Make path absolute
    return l_post

def myconvertcontent(inputcontent, source, target):
    """
    content converter
    """
    postdocument = pf.convert_text(
        inputcontent,
        input_format=source,
        output_format='panflute',
        standalone=True
    )

    pf.run_filters(
        [myimageurls, mycodeblocks],
        doc=postdocument
    )

    content = pf.convert_text(
        postdocument,
        input_format='panflute',
        output_format=target
    )

    return content

def myimageurls(elem, doc):
    """
    Panflute filter for Image URLs.
    Checks if the URLs are relative paths and match an image file. If they do,
    it uploads the image and changes the URL to point to that.
    """
    if isinstance(elem, pf.Image):
        # Handles paths if they are relative to the post
        here = os.path.dirname(doc.location)
        url = os.path.join(here, elem.url) # Make path absolute
        mime = mycheckimage(url)
        res = myuploadfile(url, mime)
        elem.url = res['url']
        return elem

# FIXME doc -> removal if possible
def mycodeblocks(elem, doc):
    """
    If input is a CodeBlock, just tag it as a code piece and put the language.
    WordPress can handle the highlighting
    """
    if isinstance(elem, pf.CodeBlock):
        content = elem.text
        language = None
        if len(elem.classes) >= 1:
            language = elem.classes[0]

        block = '[code'
        if language:
            block += ' language="%s"' % (language)
        block += ']\n%s\n[/code]' % (content)

        return pf.RawBlock(block)

def mycheckimage(url):
    """
    Checks if image path exists and if it's an image.
    @returns mime MIME type of the image or `None` if it's not an image.
    """
    if not os.path.exists(url):
        return
    mime = mimetypes.guess_type(url, strict=True)[0]
    if mime.split('/')[0] != 'image':
        # It's not an image!
        return
    return mime

def myuploadfile(url, mime):
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
    data['name'] = os.path.basename(url)
    data['type'] = mime
    with open(url) as img_file:
        data['bits'] = xmlrpc_client.Binary(img_file.read())

    my_link = mygetconfig()
    response = my_link.call(media.UploadFile(data))
    return response

def mygetallposts(offset, increment):
    """
    lets do the wordpress post listing thing
    """
    my_link = mygetconfig()

    print('============== blog entries =================')
    while True:
        posts = my_link.call(GetPosts({'number': increment, 'offset': offset}))
        if len(posts) == 0:
            break  # no more posts returned
        for l_post in posts:
            #post_str = str(post)
            #tags = ','.join(map(str,post.terms))
            # FIXME map -> list
            l_categories = ','.join(map(str, l_post.terms))
            print(l_post.id + ' - ' + l_post.title + ' - ' + l_categories)
        offset = offset + increment

def mydeletepost(postid):
    """
    delete a blogpost
    """
    my_link = mygetconfig()
    l_post = my_link.call(DeletePost(postid))
    print(l_post)

def mypublishpost(postid):
    """
    publish an existing post
    """
    # FIXME global vars -> init function
    global ARTICLE_STATUS
    my_link = mygetconfig()
    l_content = my_link.call(GetPost(postid))
    l_content.post_status = ARTICLE_STATUS
    l_post = my_link.call(EditPost(postid, l_content))
    print(l_post)

def myupdatepost(updatepostfile):
    """
    writeing back the changed content to db
    """
    my_link = mygetconfig()
    l_post = mygetpostconfig(updatepostfile)
    my_link.call(EditPost(l_post.id, l_post))

    pid = l_post.id
    print(pid.strip())

def myeditpost(postid):
    """
    edit an existing post
    """
    # loading the template file for putting
    # returned markdown into
    l_postfile = SCRIPT_DIR + '/../templates/drowmark.template'
    pfile = codecs.open(l_postfile, 'r', 'utf-8')
    buf = pfile.read()

    config = ConfigParser()
    if os.name == 'posix':
        config.read(SCRIPT_DIR + '/../.vimblogrc')
    else:
        config.read(SCRIPT_DIR + '/../_vimblogrc')

    configcategories = config.get('blog0', 'categories')

    # getting the data of the post
    my_link = mygetconfig()
    l_post = my_link.call(GetPost(postid))
    active_tags = ''
    active_categories = ''
    for term in l_post.terms:
        if term.name in configcategories:
            active_categories += term.name + ','
        else:
            active_tags += term.name + ','

    active_tags = active_tags[:-1]
    active_categories = active_categories[:-1]
    #categories = ','.join(map(str,post.categories))

    #converting the content back to markdown
    l_content = myconvertcontent(l_post.content, 'html', 'markdown')

    #fill the template
    buf = buf.replace('{ID}', l_post.id)
    buf = buf.replace('{TITLE}', l_post.title)
    buf = buf.replace('{STATUS}', l_post.post_status)
    buf = buf.replace('{CATEGORIES}', active_categories)
    buf = buf.replace('{TAGS}', active_tags)
    buf = buf.replace('{CONTENT}', l_content)

    tmp_file = tempfile.NamedTemporaryFile(suffix=l_post.id, prefix='vwp_edit', delete=False)
    filename = tmp_file.name
    tmp_file.close()
    with codecs.open(filename, 'w+b', encoding='utf-8') as file_handle:
        file_handle.write(buf)
        file_handle.seek(0)

    print(file_handle.name)

def mynewpost(s_postfile):
    """
    writing a new blog post
    """
    my_link = mygetconfig()
    l_newpost = mygetpostconfig(s_postfile)

    if l_newpost.entrytype != 'page':
        l_post = WordPressPost()
    else:
        l_page = WordPressPage()

    l_content = myconvertcontent(l_newpost.content, 'markdown', 'html')

    if l_newpost.entrytype != 'page':
        # Set post metadata
        l_post.title = l_newpost.title
        l_post.content = l_content
        l_post.post_status = l_newpost.post_status
        l_post.terms_names = l_newpost.terms_names
    else:
        # i just do the same for pages
        # except we dont need the tags
        l_page.title = l_newpost.title
        l_page.content = l_content
        l_page.post_status = l_newpost.post_status

    if l_newpost.thumb_url != None:
        thumb_mime = mycheckimage(l_newpost.thumb_url)
        if thumb_mime != None:
            l_response = myuploadfile(l_newpost.thumb_url, thumb_mime)
            if l_newpost.entrytype != 'page':
                l_post.thumbnail = l_response['id']
            else:
                l_page.thumbnail = l_response['id']

    l_out = None
    if l_newpost.entrytype != 'page':
        l_post.id = my_link.call(NewPost(l_post)) # Post it!
        l_out = l_post
    else:
        l_page.id = my_link.call(NewPost(l_page)) # or maybe post a page!
        l_out = l_page

    print("Posted: " + l_out.title)
    print("\nWith Status: " + l_out.post_status)
    print("\nAnd ID: " + l_out.id)

if __name__ == '__main__':
    # Get arguments from sys.argv, the idea is to
    # maintain it simple, making the python file
    # callable from outside VIM also.
    if len(sys.argv) != 3:
        print('calling parameter missing')
        raise BaseException
    else:
        # FIXME put switches for all functions here
        if sys.argv[2] == 'post':
            mynewpost(sys.argv[1])
        elif sys.argv[2] == 'edit':
            myeditpost(sys.argv[1])
        elif sys.argv[2] == 'publish':
            mypublishpost(sys.argv[1])
        elif sys.argv[2] == 'delete':
            mydeletepost(sys.argv[1])
        else:
            mygetallposts(sys.argv[1], sys.argv[2])

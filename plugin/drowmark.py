"""
wordpress handler
"""
from __future__ import print_function

from codecs import open as copen
from gc import enable, collect
from os import path, listdir, remove, name
from sys import argv
from io import StringIO
from tempfile import NamedTemporaryFile
from mimetypes import guess_type

ERR = ''
try:
    from configparser import ConfigParser
except:
    ERR += 'configparser module is missing'

try:
    from wordpress_xmlrpc import Client, WordPressPost, WordPressPage
    from wordpress_xmlrpc.methods.posts import NewPost, EditPost, DeletePost, GetPost, GetPosts
    from wordpress_xmlrpc.compat import xmlrpc_client
    from wordpress_xmlrpc.methods import media
except:
    ERR += 'python-wordpress-xmlrpc module is missing'

try:
    import panflute as pf
except:
    ERR += ('panflute module is missing')

if ERR != '':
    raise ERR

class Params(object):
    """
    important parameters for the initialisation
    objectified
    """
    url = ''
    username = ''
    password = ''
    article_status = ''
    categories = ''

    def __init__(self, url, username, password, article_status, categories):
        self.url = url
        self.username = username
        self.password = password
        self.article_status = article_status
        self.categories = categories

    def first(self):
        """
        placeholder for pylint
        """
        return self

    def second(self):
        """
        placeholder for pylint
        """
        return self

def getparams():
    """
    define some base params for returnage...
    """
    script_dir = path.dirname(path.realpath(__file__))
    #output.HOME = os.path.expanduser('~')
    return script_dir

def myremovefiles(s_path, pid):
    """
    just remove some files by wildcard
    """
    files = listdir(s_path)
    for fileentries in files:
        if fileentries.endswith(pid):
            remove(path.join(path, fileentries))

def mygetlink(params):
    """
    read configuration and return a set wordpress link
    """
    my_link = Client(params.url, params.username, params.password)
    return my_link

def mygetconfig(s_script_dir):
    """
    grab config variables...
    """
    config = ConfigParser()
    if name == 'posix':
        config.read(s_script_dir + '/../.vimblogrc')
    else:
        #this should cover windows
        config.read(s_script_dir + '/../_vimblogrc')

    url = config.get('blog0', 'url')
    url = 'https://' + url + '/xmlrpc.php'
    username = config.get('blog0', 'username')
    password = config.get('blog0', 'password')
    article_status = config.get('blog0', 'article_status')
    categories = config.get('blog0', 'categories')
    output = Params(url, username, password, article_status, categories)
    return output

def mygetpostconfig(s_postfile, my_link=None):
    """
    putting this into a separate function might help later on
    with cleanup.
    """
    l_post = WordPressPost()
    postconfig = ''
    postcontent = ''

    inheader = True
    tmp_file = copen(s_postfile, 'r', 'utf-8')
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

    #convert back to html
    l_content = myconvertcontent(postcontent, 'markdown', 'html', my_link)

    l_post.terms_names = {}
    l_post.tags = config.get('wordpress', 'tags')
    l_post.terms_names['post_tag'] = list(lambda x: x.strip(), l_post.tags.split(','))
    l_post.categories = config.get('wordpress', 'categories')
    l_post.terms_names['category'] = list(lambda x: x.strip(), l_post.categories.split(','))
    l_post.post_status = config.get('wordpress', 'status')
    l_post.title = config.get('wordpress', 'title')
    l_post.entrytype = config.get('wordpress', 'type')
    l_post.id = config.get('wordpress', 'id')
    l_post.content = l_content
    l_post.thumb_url = None
    if config.has_option('wordpress', 'thumbnail'):
        l_post.thumbnail = config.get('wordpress', 'thumbnail')
        here = path.dirname(s_postfile)
        l_post.thumb_url = path.join(here, l_post.thumbnail) # Make path absolute
    return l_post

def myconvertcontent(inputcontent, source, target, my_link=None):
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
        doc=postdocument,
        my_link=my_link
    )

    content = pf.convert_text(
        postdocument,
        input_format='panflute',
        output_format=target
    )

    return content

def myimageurls(elem, doc, my_link=None):
    """
    Panflute filter for Image URLs.
    Checks if the URLs are relative paths and match an image file. If they do,
    it uploads the image and changes the URL to point to that.
    """
    if isinstance(elem, pf.Image):
        # Handles paths if they are relative to the post
        here = path.dirname(doc.location)
        url = path.join(here, elem.url) # Make path absolute
        mime = mycheckimage(url)
        res = myuploadfile(url, mime, my_link)
        elem.url = res['url']
        return elem

def mycodeblocks(elem, doc, my_link=None):
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
    if not path.exists(url):
        return
    mime = guess_type(url, strict=True)[0]
    if mime.split('/')[0] != 'image':
        # It's not an image!
        return
    return mime

def myuploadfile(url, mime, my_link=None):
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
    with open(url) as img_file:
        data['bits'] = xmlrpc_client.Binary(img_file.read())

    #my_link = mygetlink()
    response = my_link.call(media.UploadFile(data))
    return response

def mygetallposts(offset, increment, my_link=None):
    """
    lets do the wordpress post listing thing
    """
    print('============== blog entries =================')
    while True:
        posts = my_link.call(GetPosts({'number': increment, 'offset': offset}))
        if len(posts) == 0:
            break  # no more posts returned
        for l_post in posts:
            #post_str = str(post)
            #tags = ','.join(map(str,post.terms))
            l_categories = ','.join(str(x) for x in l_post.terms)
            print(l_post.id + ' - ' + l_post.title + ' - ' + l_categories)
        offset = offset + increment

def mydeletepost(postid, my_link=None):
    """
    delete a blogpost
    """
    l_post = my_link.call(DeletePost(postid))
    print(l_post)

def mypublishpost(postid, config, my_link=None):
    """
    publish an existing post
    """
    l_content = my_link.call(GetPost(postid))
    l_content.post_status = config.article_status
    l_post = my_link.call(EditPost(postid, l_content))
    print(l_post)

def myupdatepost(updatepostfile, my_link=None):
    """
    writeing back the changed content to db
    """
    l_post = mygetpostconfig(updatepostfile, my_link)
    my_link.call(EditPost(l_post.id, l_post))
    pid = l_post.id
    print(pid.strip())

def myeditpost(postid, script_dir, config, my_link=None):
    """
    edit an existing post
    """
    # loading the template file for putting
    # returned markdown into
    l_postfile = script_dir + '/../templates/drowmark.template'
    pfile = copen(l_postfile, 'r', 'utf-8')
    buf = pfile.read()
    categories = config.categories

    # getting the data of the post
    l_post = my_link.call(GetPost(postid))
    active_tags = ''
    active_categories = ''
    for term in l_post.terms:
        if term.name in categories:
            active_categories += term.name + ','
        else:
            active_tags += term.name + ','

    active_tags = active_tags[:-1]
    active_categories = active_categories[:-1]
    #categories = ','.join(map(str,post.categories))

    #converting the content back to markdown
    l_content = myconvertcontent(l_post.content, 'html', 'markdown', my_link)

    #fill the template
    buf = buf.replace('{ID}', l_post.id)
    buf = buf.replace('{TITLE}', l_post.title)
    buf = buf.replace('{STATUS}', l_post.post_status)
    buf = buf.replace('{CATEGORIES}', active_categories)
    buf = buf.replace('{TAGS}', active_tags)
    buf = buf.replace('{CONTENT}', l_content)

    tmp_file = NamedTemporaryFile(suffix=l_post.id, prefix='vwp_edit', delete=False)
    filename = tmp_file.name
    tmp_file.close()
    with copen(filename, 'w+b', encoding='utf-8') as file_handle:
        file_handle.write(buf)
        file_handle.seek(0)

    print(file_handle.name)

def mynewpost(s_postfile, my_link=None):
    """
    writing a new blog post
    """
    l_newpost = mygetpostconfig(s_postfile, my_link)

    if l_newpost.entrytype != 'page':
        l_post = WordPressPost()
    else:
        l_page = WordPressPage()

    l_content = myconvertcontent(l_newpost.content, 'markdown', 'html', my_link)

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

    #l_out = None
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
    # enable garbage collection
    enable()

    # Get arguments from sys.argv, the idea is to
    # maintain it simple, making the python file
    # callable from outside VIM also.
    if len(argv) < 3:
        print('calling parameter missing')
        raise BaseException
    else:
        #global params
        PARAMS = getparams()
        #config file variables
        CONFIGVARS = mygetconfig(PARAMS)
        #wordpress connection
        LINK = mygetlink(CONFIGVARS)
        if argv[2] == 'post':
            mynewpost(argv[1], LINK)
        elif argv[2] == 'edit':
            myeditpost(argv[1], PARAMS, CONFIGVARS, LINK)
        elif argv[2] == 'update':
            myupdatepost(argv[1], LINK)
        elif argv[3] == 'removefiles':
            myremovefiles(argv[1], argv[2])
        elif argv[2] == 'publish':
            mypublishpost(argv[1], CONFIGVARS, LINK)
        elif argv[2] == 'delete':
            mydeletepost(argv[1], LINK)
        elif argv[3] == 'list':
            mygetallposts(argv[1], argv[2], LINK)
        else:
            print("no option chosen")

    # deleting unused stuff
    del PARAMS, CONFIGVARS, LINK
    # force collect at end of program
    collect()
    #and force leave the program for security
    exit(0)

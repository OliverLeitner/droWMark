# droWMark

Vim plugin to post from VIM to WordPress using
[Pandoc-Markdown](http://pandoc.org/README.html#pandocs-markdown).

It uses an special template in files, they are a mix between an INI header and
a MarkDown content. There is a template in `templates` directory.

## How to

Install the plugin using Vundle, Pathogen (or other package management tool) or
Manually. (see below)

Configure your blog using (this will write a file called either .vimblogrc or 
_vimblogrc in the root in the root directory of this plugin:


```
:ConfigWordPress
```

When the plugin is installed, you can create a new blog entry using:

```
:NewWordPress
```

This will insert the template file in the file you are editing and switch the
filetype to `drowmark` which automatically activates the `drowmark` syntax
highlighting. This filetype is also activated when the extension of the file is
`.wp`. The template contains all the information needed to fill the
configuration part.

When the blog entry is finished, it is possible to post in WordPress with the
following command:

```
:PostWordPress
```

To get a list of available posts i.e. if you want to edit or publish or 
delete an existing entry, please use:

```
:ListWordPress
```

To edit an existing blog post:

```
:EditWordPress
```

This will ask you for the blog id you want to edit, you will find the blog ids 
available to you with the above command :ListWordPress

After editing a post, you might want to update it on the blog, to do so use:

```
:UpdateWordPress
```

To delete an existing post, use:

```
:DeleteWordPress
```

And last but not least, to publish your post, type:

```
:PublishWordPress
```

### Upload Images

All the URLs of the images are checked. If the URL of the image is a relative
path to a local image, it's uploaded *automagically* and the URL is changed to
the uploaded media file URL.

## Installation

Installation could be done using a plugin manager or manually.

### Manual installation

Copy the directories in you `.vim` folder and you are done. Keep the
directories in the correct order. For example, put all the files in `ftplugin`
folder inside `.vim/ftplugin` and so on.

### Plugin manager installation

Most of the plugin managers, like Vundle (I recommend this one) are able to
download the code of the plugin from gitHub and install it correctly, putting
the directory tree under `.vim/bundle/droWMark` directory.

### Dependencies

It is necessary to have Vim compiled with `+python` or `+python3` option.

Dependencies for the python script are:

- future package, for full compatibility with all python 2 and 3 versions
  `apt install python-future`

- Panflute package, wich also depends on Pandoc  
  `pip install panflute`
  or
  `pip3 install panflute`

- Wordpress XML RPC  
  `pip install python-wordpress-xmlrpc`
  or
  `pip3 install python-wordpress-xmlrpc`

- ConfigParser package  
  `apt install python-configparser`

## Notes

### Vim independent

It keeps python code as separate as possible from VIM. Python code is also
callable from outside with the same functionality. VIM is only an interface to
insert the parameters correctly.

### Useful links for writing plugins

- [How to write vim plugins](http://stevelosh.com/blog/2011/09/writing-vim-plugins/)

- [Python in vim plugins](http://vimdoc.sourceforge.net/htmldoc/if_pyth.html#:pyfile)

- [XML-RPC WordPress](http://python-wordpress-xmlrpc.readthedocs.org/en/latest/overview.html)

- [Syntastic help file](https://github.com/scrooloose/syntastic/blob/master/doc/syntastic.txt)

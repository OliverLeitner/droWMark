# droWMark

Vim plugin to post from VIM to WordPress using
[Pandoc-Markdown](http://pandoc.org/README.html#pandocs-markdown).

It uses an special template in files, they are a mix between an INI header and
a MarkDown content. There is a template in `templates` directory.

## How to

Install the plugin using Vundle, Pathogen (or other package management tool) or
Manually. (see below)

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

This will ask for the username and the password before publishing the post in
WordPress.

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

It is necessary to have Vim compiled with `+python` option.

Dependencies for the python script are:

- Panflute package, wich also depends on Pandoc  
  `pip install panflute`

- Wordpress XML RPC  
  `pip install python_wordpress_xmlrpc`

- ConfigParser package  
  `pip install configparser`

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

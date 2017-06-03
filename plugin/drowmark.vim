" Prepare arguments for python script.
let s:inter=''
if( has('python3') )
    let s:inter='python3'
elseif( has('python') )
    let s:inter='python'
else
    echo "No python interpreter"
endif

"offset and increment for list blog entries
"this could be given by commandline or from config file or by math in case of
"offset...
let s:increment = 20
let s:offset = 0

"dynamic temporary directories
let s:tmp = ''
"dynamic config file path
let s:file = ''
let s:operate = s:inter . ' -c "from __future__ import print_function; import os; print(os.name)"'
let s:os = system(s:operate)

"im only running gnu, more to come, options are
if s:os =~ 'posix'
    let s:tmp = escape('/tmp','\')
    let s:file = '.vimblogrc'
endif

let s:path = escape(resolve(expand('<sfile>:p:h')),'\')
let s:script = escape(s:path, ' ') . '/drowmark.py'

function! PostWordPress()
    let l:writepath = s:tmp . '/saveEntry'
    exec 'write ' . l:writepath
    let l:blogpost = '!' . s:inter . ' ' . s:script . ' ' . l:writepath . ' post'
    execute l:blogpost
    let l:dupp = s:inter . ' -c "import os; os.unlink(\"'.s:tmp.'/saveEntry\")"'
    let l:dupp2 = system(l:dupp)
    exec 'q!'
endfunction

function! NewWordPress()
    let l:template = escape(s:path, ' ') . '/../templates/drowmark.template'
    exec 'read '. l:template
    setlocal ft=drowmark
endfunction

" Get a list of blog entries from our blog
function! ListWordPress()
    silent execute '!clear'
    let l:bloglist = '!' . s:inter . ' ' . s:script . ' ' . s:offset . ' ' . s:increment
    execute l:bloglist
endfunction

"publish an existing post
function! PublishWordPress()
    call inputsave()
    let l:postid = input('Enter a post ID to publish: ')
    call inputrestore()
    let l:publish = '!' . s:inter . ' ' . s:script . ' ' . l:postid . ' publish'
    execute l:publish
endfunction

"update an existing post to db
function! UpdateWordPress()
    silent! exec 'write '. s:tmp .'/updatePost'
    silent! exec 'close'
    let l:update = s:inter . ' -c "from __future__ import print_function; import sys; import os; sys.path.append(os.path.abspath(\"'.s:path.'\")); import drowmark as dwm; dwm.myupdatepost(\"'.s:tmp.'/updatePost\")"'
    let l:tmpname = system(l:update)
    let l:tmpname2 = systemlist('echo '.l:tmpname)[0]
    let l:dupp = s:inter . ' -c "import os; os.unlink(\"'.s:tmp.'/updatePost\")"'
    let l:dupp2 = system(l:dupp)
    let l:delpid = s:inter . ' -c "from __future__ import print_function; import sys; import os; sys.path.append(os.path.abspath(\"'.s:path.'\")); import drowmark as dwm; dwm.myremovefiles(\"'.s:tmp.'\",\"'.l:tmpname2.'\")"'
    let l:delpid2 = system(l:delpid)
endfunction!

"edit an existing post
function! EditWordPress()
    call inputsave()
    let l:postid = input('Enter a post ID to edit: ')
    call inputrestore()
    let l:buffer = s:inter . ' ' . s:script . ' ' . l:postid . ' edit'
    let l:name = system(l:buffer)
    if winnr() > 1
        exec 'read '. l:name
    else
        exec 'vertical new'. l:name
        exec 'vertical resize +60'
    endif
    setlocal ft=drowmark
endfunction

"delete an existing post
function! DeleteWordPress()
    call inputsave()
    let l:postid = input('Enter a post ID to delete: ')
    call inputrestore()
    let l:delete = s:inter . ' ' . s:script . ' ' . l:postid . ' delete'
    execute l:delete
endfunction

"writing the base configuration
"kind of a setuptool
function! ConfigWordPress()
    call inputsave()
    let l:url = input('Please enter the name of your blog: ')
    call inputrestore()
    echo "\n"
    call inputsave()
    let l:categories = input('Which categories does your blog cover: ')
    call inputrestore()
    echo "\n"
    call inputsave()
    let l:article_status = input('Do you directly publish (publish) or are you just an editor (draft): ')
    call inputrestore()
    echo "\n"
    call inputsave()
    let l:username = input('Please enter your blog username: ')
    call inputrestore()
    echo "\n"
    echo "Please enter your blogs password: "
    let l:password = s:getPass()
    let l:message = "[blog0]\nurl = ".l:url."\nusername = ".l:username."\npassword = ".l:password."\ncategories = ".l:categories."\narticle_status = ".l:article_status
    call ConfigFileWordPress(l:message)
endfunction

function! ConfigFileWordPress(message)
    setlocal buftype=nofile bufhidden=hide noswapfile nobuflisted
    put=a:message
    execute 'wq '. s:path .'/../'.s:file
endfunction

" Get password without showing the echo in the screen
function! s:getPass()
    let password = ""
    let char = nr2char(getchar())
    while char !=  "\<CR>"
        let password = password . char
        let char = nr2char(getchar())
    endwhile
    return password
endfunction

command! ListWordPress call ListWordPress()
command! PublishWordPress call PublishWordPress()
command! UpdateWordPress call UpdateWordPress()
command! EditWordPress call EditWordPress()
command! DeleteWordPress call DeleteWordPress()
command! NewWordPress call NewWordPress()
command! PostWordPress call PostWordPress()
command! ConfigWordPress call ConfigWordPress()

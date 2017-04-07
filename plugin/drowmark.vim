function! PostWordPress()
    " Prepare arguments for python script.
    if( has('python') )
        let inter='python'
        let interfile='pyfile'
    else
        return "No python interpreter"
    endif
    exe inter . ' ' .'import vim'
    exe inter . ' ' .'import sys'
    let l:script = escape(s:path, ' ') . '/drowmark.py'
    exe inter.' ' . 'sys.argv = [ vim.eval("l:script"), vim.eval("@%") ]'
    " Call script
    exe interfile .' ' . l:script
endfunction

function! NewWordPress()
    let l:template = escape(s:path, ' ') . '/../templates/drowmark.template'
    exec 'read '. l:template
    setlocal ft=drowmark
endfunction

" Get a list of blog entries from our blog
function! ListWordPress()
    silent execute '!clear'
    let l:bloglist = '!python -c "import sys; import os; sys.path.append(os.path.abspath(\"'.s:path.'\")); import drowmark as dwm; dwm.getAllPosts(0,20)"'
    execute l:bloglist
    "exec 'read '. l:bloglist
    "setlocal buftype=nofile
endfunction

"publish an existing post
function! PublishWordPress()
    call inputsave()
    let l:postid = input('Enter a post ID to publish: ')
    call inputrestore()
    let l:publish = '!python -c "import sys; import os; sys.path.append(os.path.abspath(\"'.s:path.'\")); import drowmark as dwm; dwm.publishPost('.l:postid.')"'
    execute l:publish
endfunction

"update an existing post to db
function! UpdateWordPress()
    silent! exec 'write '.s:tmp.'/updatePost'
    silent! exec 'close'
    let l:update = 'python -c "import sys; import os; sys.path.append(os.path.abspath(\"'.s:path.'\")); import drowmark as dwm; dwm.updatePost(\"'.s:tmp.'/updatePost\")"'
    let l:tmpname = system(l:update)
    let l:tmpname2 = systemlist('echo '.l:tmpname)[0]
    let l:dupp = 'python -c "import os; os.unlink(\"'.s:tmp.'/updatePost\")"'
    let l:dupp2 = system(l:dupp)
    let l:delpid = 'python -c "import sys; import os; sys.path.append(os.path.abspath(\"'.s:path.'\")); import drowmark as dwm; dwm.removefiles(\"'.s:tmp.'\",\"'.l:tmpname2.'\")"'
    let l:delpid2 = system(l:delpid)
    "exec l:delpid
endfunction!

"edit an existing post
function! EditWordPress()
    call inputsave()
    let l:postid = input('Enter a post ID to edit: ')
    call inputrestore()
    let l:buffer = 'python -c "import sys; import os; sys.path.append(os.path.abspath(\"'.s:path.'\")); import drowmark as dwm; dwm.editPost('.l:postid.')"'
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
    let l:delete = '!python -c "import sys; import os; sys.path.append(os.path.abspath(\"'.s:path.'\")); import drowmark as dwm; dwm.deletePost('.l:postid.')"'
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
    echom s:file
    execute 'wq '.s:path.'/../'.s:file
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

function! DoTest()
    echom s:path
endfunction

"dynamic temporary directories
let s:tmp = ''
"dynamic config file path
let s:file = ''
let s:operate = 'python -c "import os; print os.name"'
let s:os = system(s:operate)

"im only running gnu, more to come, options are
if s:os =~ 'posix'
    let s:tmp = escape('/tmp','\')
    let s:file = '.vimblogrc'
endif

let s:path = escape(resolve(expand('<sfile>:p:h')),'\')

command! DoTest call DoTest()
command! ListWordPress call ListWordPress()
command! PublishWordPress call PublishWordPress()
command! UpdateWordPress call UpdateWordPress()
command! EditWordPress call EditWordPress()
command! DeleteWordPress call DeleteWordPress()
command! NewWordPress call NewWordPress()
command! PostWordPress call PostWordPress()
command! ConfigWordPress call ConfigWordPress()

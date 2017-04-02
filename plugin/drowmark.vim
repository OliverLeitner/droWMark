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

"delete an existing post
function! DeleteWordPress()
    call inputsave()
    let l:postid = input('Enter a post ID to delete: ')
    call inputrestore()

    let l:delete = '!python -c "import sys; import os; sys.path.append(os.path.abspath(\"'.s:path.'\")); import drowmark as dwm; dwm.deletePost('.l:postid.')"'
    execute l:delete
endfunction

let s:path = escape(resolve(expand('<sfile>:p:h')),'\')

command! ListWordPress call ListWordPress()
command! PublishWordPress call PublishWordPress()
command! DeleteWordPress call DeleteWordPress()
command! NewWordPress call NewWordPress()
command! PostWordPress call PostWordPress()

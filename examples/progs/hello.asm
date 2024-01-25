.data
curr_sym_ptr: 0
last_sym_ptr: 0

str_ptr: 'Hello World!'

.text
main:   ld    str_ptr
        call  print
        hlt


print:  st    curr_sym_ptr
        add  ~curr_sym_ptr
        st    last_sym_ptr
p_loop: ld    curr_sym_ptr
        inc
        st    curr_sym_ptr
        cmp   last_sym_ptr
        jgt   exit_l
        ld   ~curr_sym_ptr
        out
        jump  p_loop
exit_l: ret


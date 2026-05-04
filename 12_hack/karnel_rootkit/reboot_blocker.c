#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/init.h>

// Indirizzo trovato con grep nel tuo System.map
unsigned long *sys_call_table_address;

static int __init startup(void) 
{
    sys_call_table_address = (unsigned long *)0xffffffff81401200;
    
    // Stampiamo un messaggio per confermare l'avvio nel dmesg
    printk(KERN_NOTICE "EHROOTKIT: Modulo caricato. Tabella a: %p\n", sys_call_table_address);
    
    return 0; // Fondamentale: deve tornare 0 per avere successo
}

static void __exit shutdown(void) 
{
    printk(KERN_NOTICE "EHROOTKIT: Modulo rimosso\n");
}

module_init(startup); 
module_exit(shutdown); 
MODULE_LICENSE("GPL");

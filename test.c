#include <linux/init.h>
#include <linux/module.h>
#include <linux/proc_fs.h>
#include <linux/uaccess.h>
#include <linux/slab.h>

#define MY_DEV_NAME "test"
#define DEBUG_FLAG "PROC_DEV"

static ssize_t proc_read (struct file *proc_file, char __user *proc_user, size_t n, loff_t *loff);
static ssize_t proc_write (struct file *proc_file, const char __user *proc_user, size_t n, loff_t *loff);
static int proc_open (struct inode *proc_inode, struct file *proc_file);
static struct proc_ops a = {
                                .proc_open = proc_open,
                                .proc_read = proc_read,
                                .proc_write = proc_write,
};


static int __init mod_init(void)
{
    struct proc_dir_entry *test_entry;
    const struct proc_ops *proc_fops = &a;
    printk(DEBUG_FLAG":proc init start!\n");

    test_entry = proc_create(MY_DEV_NAME, S_IRUGO|S_IWUGO, NULL, proc_fops);
    if(!test_entry)
       printk(DEBUG_FLAG":there is somethings wrong!\n");
    
    printk(DEBUG_FLAG":proc init over!\n");
    return 0;
}

static ssize_t proc_read (struct file *proc_file, char __user *proc_user, size_t n, loff_t *loff)
{
    printk(DEBUG_FLAG":finish copy_from_use,the string of newbuf is");

    return 0;
}

static ssize_t proc_write (struct file *proc_file, const char __user *proc_user, size_t n, loff_t *loff)
{
    char *c = kmalloc(n + 512, GFP_KERNEL);

    size_t size = copy_from_user(c, proc_user, n + 4096);
    printk(DEBUG_FLAG":into write %ld!\n", size);
    return 0;
}

int proc_open (struct inode *proc_inode, struct file *proc_file)
{
    printk(DEBUG_FLAG":into open!\n");
    return 0;
}

module_init(mod_init);

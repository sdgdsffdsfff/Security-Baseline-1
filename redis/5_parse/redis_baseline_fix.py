import getopt
import os
import re
import sys
sys.path.append('../../')
from common.baseline_fix import GenFixScript


class GenRedisFixScript(GenFixScript):
    def __init__(self,argv,ip_addr):
        baseline_type = "Redis"
        base_dir = "/etc/mysql/mysql.conf.d"
        super().__init__(argv,ip_addr,baseline_type,base_dir)

    def gen_shell_script_usage(self):
        self.shell_script_obj.writelines("""
usage(){
  echo "
Usage:
  -s, --server_path     redis_server absolutely path, default /opt/redis-5.0/bin/redis-server
  -c, --conf_path       redis config file, default /opt/redis-5.0/conf/redis.conf
  -p, --password        the password to set while redis have no password, default t*tsrch0st
  -h, --help            display this help and exit

  example1: bash redis_fix.sh -s/opt/redis-5.0/bin/redis-server -c/opt/redis-5.0/conf/redis.conf -pt*tsrch0st
  example2: bash redis_fix.sh --server_path=/opt/redis-5.0/bin/redis-server --conf_path=/opt/redis-5.0/conf/redis.conf --password=t*tsrch0st
"
}

main_pre(){
    # set -- $(getopt i:p:h "$@")
    set -- $(getopt -o s:c:p:h --long server_path:,conf_path:,password:,help -- "$@")
    ipaddr=`ifconfig|grep 'inet'|grep -v '127.0.0.1'|awk '{print $2}'|cut -d':' -f 2`
    id=0
    SERVER_PATH='/opt/redis-5.0/bin/redis-server'
    CONF_PATH='/opt/redis-5.0/conf/redis.conf'
    PASSWORD="t*tsrch0st"

    while true
    do
      case "$1" in
      -s|--server_path)
          SERVER_PATH="$2"
          shift
          ;;
      -c|--conf_path)
          CONF_PATH="$2"
          shift
          ;;
      -p|--password)
          PASSWORD="$2"
          shift
          ;;
      -h|--help)
          usage
          exit
          ;;
      --)
        shift
        break
        ;;
      *)
        echo "$1 is not option"
        ;;
      esac
      shift
    done
    xml_file_name="/tmp/${ipaddr}_redis_fix.log"
}""")

    def gen_shell_script_set_redis_password(self, fix_object, fix_comment, check_result):
        fix_command = ""
        for line in check_result:
            dir_name = line.split()[-1]
            fix_command += f"echo -e \\\"requirepass $PASSWORD\\\" >> $CONF_PATH"
        self.shell_script_obj.writelines("""
fixMysqlRunner(){
    fix_object=\"""" + fix_object + """\"
    fix_comment=\"""" + fix_comment + """\"
    fix_command=\"""" + fix_command + """\"
    fix_result=`eval $fix_command`
    appendToXml "$fix_object" "$fix_command" "$fix_comment" "$fix_result"
}
        """)


    def gen_shell_script_main_part(self):
        need_fix_item = self.html_obj.html.xpath("//div[@class = 'card-header bg-danger text-white']/..")
        # need_fix_item = self.html_obj.html.xpath("//div[contains(@class, 'card-header')]/..")
        # all_need_fix_items = all_item_div.xpath("//div[@class='card-header bg-danger text-white']/..")
        # gg=self.soup.find_all(id="accordion2")
        for item in need_fix_item:
            check_title=item.xpath("div//a/text()")[0]
            check_object=item.xpath("div//table/tr[1]/td/text()")[0]
            check_command=item.xpath("div//table/tr[2]/td/text()")[0]
            check_comment = item.xpath("div//table/tr[3]/td/text()")[0]
            check_result = item.xpath("div//table/tr[4]/td/text()")
            if check_title == "为redis设置密码":
                self.gen_shell_script_set_redis_password(check_object,check_comment,check_result)
                self.fix_item_list["gen_shell_script_change_mysql_runner"] = "fixMysqlRunner"
                continue

    def gen_shell_script(self):
        self.gen_shell_script_head_part()
        self.gen_shell_script_main_part()
        self.gen_shell_script_usage()
        self.gen_shell_script_tail_part()



if __name__ == "__main__":
    argv = sys.argv[1:]
    ip_reg = "(\d{1,3}\.{1}){3}\d{1,3}"
    full_reg = f"{ip_reg}_redis_report\.html"
    pwd_file_list = os.listdir("../4_report")
    for file in pwd_file_list:
        if re.search(full_reg, file):
            ip_addr = re.search(ip_reg, file).group()
            obj = GenRedisFixScript(argv, ip_addr)
            obj.gen_shell_script()
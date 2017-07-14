#!/bin/bash

pscu_account='pscu'
pscu_account_name='PSCU User'
pscu_hostname='pscu'
pscu_home=/home/${pscu_account}
pscu_venv=${pscu_home}/venv

github_url='https://github.com/stfc-aeg/odin-lpdpower'
lpdpower_dir=${pscu_home}/odin-lpdpower

timezone='Europe/London'

ntp_servers="time.rl.ac.uk"

def_account_groups=''

check_root ()
{
    if [[ $EUID -ne 0 ]]; then
	echo "This script must be run as root" 1>&1
	exit 1
    fi
}

set_root_passwd()
{
    root_passwd_status=$(passwd -S | awk '{print $2}')
    if [ $root_passwd_status == 'NP' ]; then
	echo "No root password set, please set one now:"
	passwd
    fi
}

set_hostname()
{
    orig_hostname=$(hostname)
    changed=0

    echo "Updating host name to $pscu_hostname"

    if [ $orig_hostname != $pscu_hostname ]; then
	echo "  Setting hostname to $pscu_hostname"
	hostname $pscu_hostname
	changed=1
    fi

    etc_hostname='/etc/hostname'
    if [ $(cat $etc_hostname) != $pscu_hostname ]; then
	echo "  Setting hostname in $etc_hostname to $pscu_hostname"
	mv -f $etc_hostname ${etc_hostname}.orig
	echo $pscu_hostname >$etc_hostname
	changed=1
    fi

    if [ $orig_hostname != $pscu_hostname ]; then
	grep -q $orig_hostname /etc/hosts
	if [ $? == 0 ]; then
	    echo "  Replacing $orig_hostname entry in /etc/hosts with $pscu_hostname"
	    sed s/$orig_hostname/$pscu_hostname/g -i.orig /etc/hosts
	    changed=1
	fi
    fi

    grep -q $pscu_hostname /etc/hosts
    if [ $? != 0 ]; then
	echo "  Adding $pscu_hostname to /etc/hosts"
	/bin/echo -e "127.0.1.1\t${pscu_hostname}.localdomain ${pscu_hostname}" >> /etc/hosts
	changed=1
    fi

    if [ $changed == 0 ]; then
	echo "  OK, no host name changes required"
    fi

}

set_timezone()
{
    echo "Setting timezone to ${timezone}"
    etc_timezone=/etc/timezone
    if [ $(cat ${etc_timezone}) != ${timezone} ]; then
	cp ${etc_timezone} ${etc_timezone}.orig
	echo ${timezone} > ${etc_timezone}
	dpkg-reconfigure -f noninteractive tzdata
    else
	echo "  OK, timezone already correctly configured"
    fi
}

update_system()
{
    echo "Updating system packages ..."
    apt-get update && apt-get -y upgrade
}

modify_runlevel()
{
    echo "Modifying runlevel and running services"
    dist_id=$(lsb_release -is)
    release_version=$(lsb_release -rs | cut -d. -f1)

    if [ ${dist_id} == 'Debian' ]; then

	if [ ${release_version} == '7' ]; then

	    echo "  Disabling sysvinit services ..."
	    sysvinit_services="xrdp apache2 rsync bluetooth lightdm saned"
	    for svc in ${sysvinit_services}; do
	    	/bin/echo -n "    ${svc}: "
	    	update-rc.d ${svc} remove
	    done

	    echo "  Disabling systemctl services ..."
	    systemctl_services="wpa_supplicant bonescript bonescript-autorun jekyll-autorun rsync"
	    for svc in ${systemctl_services}; do
		/bin/echo -n "    ${svc}: "
		systemctl disable ${svc}.service
		if [ $? == 0 ]; then
		    echo "OK"
                fi
            done

	    echo "  Forcing systemd to use multi-user target as default"
	    ln -sf /lib/systemd/system/multi-user.target /lib/systemd/system/default.target

	elif [ ${release_version} == '8' ]; then

	    systemctl_target='multi-user.target'
	    if [ $(systemctl get-default) != ${systemctl_target} ]; then
		systemctl set-default ${systemctl_target}
	    else
                echo "  OK, default systemctl target is aleady ${systemctl_target}"
            fi
	else
	    echo "  Unrecognised Debian release: {$release_version}, skipping this step"
        fi
    else
	echo "  Not a Debian distribution, skipping this step"
    fi
}

install_apt_pkgs()
{
    required_pkgs=("$@")
    install_pkgs=()

    for pkg in ${required_pkgs[@]};  do

	dpkg-query -l $pkg >/dev/null 2>&1
	if [ $? != 0 ]; then
	    install_pkgs+=($pkg)
	fi
    done

    if [ ${#install_pkgs[@]} != 0 ]; then
	echo "  Packages to install : ${install_pkgs[@]}"
	apt-get install -y ${install_pkgs[@]}
    else
	echo "  No packages to install"
    fi

}

install_mdns()
{
    echo "Installing packages to allow mDNS to function:"
    install_apt_pkgs avahi-daemon libnss-mdns
}

install_ntp()
{
    echo "Installing NTP service"
    /bin/echo -n "  Installing NTP packges: "
    install_apt_pkgs ntp ntpdate

    /bin/echo -n "  Configuring NTP servers: "
    ntp_conf=/etc/ntp.conf
    current_servers=$(grep "^server" ${ntp_conf} | cut -d ' ' -f2 | sort | tr '\n' ' ')
    wanted_servers=$(echo ${ntp_servers} | sort)
    diff <( echo ${current_servers} ) <( echo ${wanted_servers} ) >/dev/null 2>&1
    if [ $? != 0 ]; then
	cp -f ${ntp_conf} ${ntp_conf}.orig
	sed -e '/^server/ s/^#*/#/' -i ${ntp_conf}
	echo "" >> ${ntp_conf}
	for server in ${wanted_servers}; do
	    echo "server ${server} iburst" >> ${ntp_conf}
	done
	echo "OK, modified"
	/bin/echo -n "  Reloading NTP service: "
	systemctl restart ntp.service
	if [ $? == 0 ]; then
	    echo "done"
	fi
    else
	echo "no modification required"
    fi

}

install_supervisord()
{
    echo "Installing supervisord packages:"
    install_apt_pkgs supervisor

    echo "Ensuring supervisor init script checks for log directory"
    supervisor_init=/etc/init.d/supervisor
    #logdircmd='test -d $LOGDIR || mkdir -p $LOGDIR'
    grep -q 'mkdir\ -p\ \$LOGDIR'  $supervisor_init
    if [ $? != 0 ]; then
	sed '/^LOGDIR\=/ atest -d \$LOGDIR \|\| mkdir -p \$LOGDIR' -i.orig ${supervisor_init}
	echo "  Done."
    else
	echo "  OK, script already checks of existing of LOGDIR"
    fi
}

install_virtualenv()
{
    echo "Installing python virtualenv:"
    pip freeze | grep -q virtualenv
    if [ $? != 0 ]; then
	echo pip install virtualenv
    else
	echo "  Virtualenv already installed"
    fi
}

suppress_sshd_banner()
{
    echo "Suppressing SSH login banner"
    sshd_config=/etc/ssh/sshd_config
    grep -q "^Banner" $sshd_config
    if [ $? == 0 ]; then
	sed -e '/^Banner/ s/^#*/#/' -i.orig $sshd_config
	systemctl reload sshd.service
	echo "  Done: commented out Banner from ${sshd_config} and reloaded SSHD"
    else
	echo "  OK, sshd banner not configured"
    fi
}

suppress_debian_login_reminder()
{
    echo "Suppressing debian account login reminder"
    for file in /etc/issue /etc/issue.net; do
	grep -q "default username\:password" $file
	if [ $? == 0 ]; then
	    sed '/^default username\:password/d' -i.orig $file
	    echo "  Done:, removed from $file"
        else
	    echo "  OK, reminder not found in $file"
        fi
    done

}

fix_python_dist_permissions()
{
    dist_dir=/usr/local/lib/python2.7/dist-packages

    echo "Fixing python dist package permissions in ${dist_dir}"
    find ${dist_dir} -type d -exec chmod a+rx {} \;
    find ${dist_dir} -type f -exec chmod a+r {} \;
}

delete_default_account()
{

    def_account=debian

    # Temp add account to allow it to be deleted - REMOVE THIS
#    adduser --disabled-password --gecos "Debian User A,,," $def_account
#    usermod -G adm,kmem,dialout,cdrom,floppy,audio,dip,video,plugdev,users,netdev,i2c,admin,spi,systemd-journal,weston-launch,xenomai $def_account

    echo "Deleting default user account ($def_account)"
    /usr/bin/id $def_account >/dev/null 2>&1
    if [ $? == 0 ]; then
	def_account_groups=$(grep $def_account /etc/group | awk -F: '{print $1}' | grep -v $def_account)
	def_account_groups=$(echo $def_account_groups | sed 's/ /,/g')
	/bin/echo -n "  $def_account is a member of the following groups: "
	echo $def_account_groups
	deluser --remove-home $def_account
    else
	echo "  OK, no $def_account account found"
    fi
}

create_pscu_account()
{
    echo "Creating $pscu_account account"
    /usr/bin/id $pscu_account >/dev/null 2>&1
    if [ $? != 0 ]; then
	adduser --disabled-password --gecos "${pscu_account_user},,," $pscu_account
	usermod -G $def_account_groups $pscu_account
	echo "  Added $pscu_account to system"

    else
	echo "  OK, $pscu_account account already exists"
    fi

    pscu_passwd_status=$(passwd -S ${pscu_account} | awk '{print $2}')
    if [ $pscu_passwd_status == 'NP' ] || [ $pscu_passwd_status == 'L' ]; then
	echo "  No $pscu_account password set, please set one now:"
	passwd ${pscu_account}
    fi

}

create_pscu_venv()
{
    echo "Creating virtualenv in ${pscu_venv}"
    if [ ! -d ${pscu_venv} ]; then
	sudo -u ${pscu_account} /bin/bash <<EOF
            /usr/local/bin/virtualenv --system-site-packages ${pscu_venv}
EOF
    else
	echo "  OK, virtualenv already exists"
    fi
}

clone_odin_lpdpower()
{
    echo "Cloning github repo lpdpower ($github_url} into ${lpdpower_dir}"
    if [ ! -d ${lpdpower_dir} ]; then
	sudo -u ${pscu_account} /bin/bash <<EOF
            cd ${pscu_home}
            git clone ${github_url}
EOF
    else
	echo "  OK, ${lpdpower_dir} already exists"
    fi

}

install_odin_lpdpower()
{
    echo "Installing odin_lpdpower"
    sudo -u ${pscu_account} /bin/bash <<EOF
        source ${pscu_venv}/bin/activate
        cd ${lpdpower_dir}
        ${pscu_venv}/bin/python setup.py install
EOF
}

set_pscu_splashscreen()
{
    echo "Setting PSCU LCD splash screen"
    sudo -u ${pscu_account} /bin/bash <<EOF
        /bin/echo -n "  "
        ${lpdpower_dir}/scripts/lcdsetsplash
EOF
}

install_pscu_startup()
{
    echo "Installing PSCU startup scripts"

    /bin/echo -n "  Copying LCD boot message service script: "
    /usr/bin/install -v -b -t /etc/systemd/system ${lpdpower_dir}/etc/systemd/system/lcdbootmsg.service
    /bin/echo -n "  Enabling in systemd: "
    systemctl enable lcdbootmsg.service
    if [ $? == 0 ]; then
	echo "done"
    fi

    /bin/echo -n "  Copying PSCU supervisord config file: "
    /usr/bin/install -v -b -t /etc/supervisor/conf.d ${lpdpower_dir}/etc/supervisor/conf.d/pscu.conf

    /bin/echo -n "  Reloading supervisord configuration: "
    supervisorctl reload

    /bin/echo -n "  Checking PSCU is running: "
    retries=0
    max_retries=5
    while [ $retries -lt $max_retries ]; do
	pscu_status=$(supervisorctl status pscu | awk '{print $2}')
	if [ $pscu_status != 'STARTING' ]; then
	    break
	fi
	sleep 1
	((retries++))
    done
    if [ $pscu_status != 'RUNNING' ] || [ ${retries} -ge ${max_retries} ]; then
	echo "Error - PSCU failed to start up, status is currently ${pscu_status}"
    else
	echo "OK"
    fi
}

create_tempfs_fstab_entry()
{
    fstab_file=$1
    mnt_point=$2
    mode=$3
    size=$4

    fstab_file_modified=0

    file_entry=$(grep ${mnt_point} ${fstab_file})
    if [ $? != 0 ]; then
	/bin/echo -n "  Adding ${mnt_point} tmpfs entry to ${fstab_file}: "
	echo "tmpfs $entry ${mnt_point} tmpfs defaults,noatime,nosuid,mode=${mode},size=${size} 0 0 ">> ${fstab_file}
	fstab_file_modified=1
	echo "done"
    else
	fstype=$(echo ${file_entry} | awk '{print $1}')
	if [ "$fstype" == 'tmpfs' ]; then
	    echo "  OK, ${fstab_file} already has a tmpfs entry for ${mnt_point}"
	else
	    echo "  WARNING, ${fstab_file} has an entry for ${mnt_point} but it does not appear to be of type tmpfs"
	fi
    fi

    return $fstab_file_modified
}

set_rootfs_readonly()
{
    echo "Setting up root file system as read-only"
    etc_fstab=/etc/fstab
    fstab_modified=0

    orig_fstab=$(mktemp /tmp/etc_fstab_orig.XXXXX)
    cp -f $etc_fstab ${orig_fstab}


    root_mntops=$(grep " / " $etc_fstab | awk '{print $4}' | sed 's/,/ /g')
    has_ro_opt=0
    for opt in $root_mntops; do
	if [ $opt == 'ro' ]; then
	    has_ro_opt=1
	    break
	fi
    done
    if [ $has_ro_opt == 0 ]; then
	/bin/echo -n "  Adding read-only option to rootfs entry in $etc_fstab: "
	tmp_fstab=$(mktemp /tmp/etc_fstab.XXXXX)
	cat $etc_fstab > $tmp_fstab
	cat $tmp_fstab | awk '/\ \/\ /{$4="ro,"$4}{print}' > $etc_fstab
	rm -f ${tmp_fstab}
	fstab_modified=1
	echo "done"
    else
	echo "  OK, rootfs entry is $etc_fstab is already marked for read-only"
    fi

    create_tempfs_fstab_entry ${etc_fstab} '/var/log'  '1777' '128M'
    create_tempfs_fstab_entry ${etc_fstab} '/var/lib/dhcp' '1777' '1M'
    create_tempfs_fstab_entry ${etc_fstab} '/var/lib/sudo' '0700' '1M'
    create_tempfs_fstab_entry ${etc_fstab} '/tmp' '1777' '32M'

    if [ $fstab_modified != 0 ]; then
	echo "  Making backup copy of ${etc_fstab} to ${etc_fstab}.orig"
	cp -f ${orig_fstab} ${etc_fstab}.orig
    fi
    rm -f ${orig_fstab}
}

echo "*******************************************"
echo "*                                         *"
echo "*    XFEL LPD PSCU Installation Script    *"
echo "*                                         *"
echo "*******************************************"
echo

check_root
set_root_passwd
set_hostname
set_timezone
update_system
modify_runlevel
install_mdns
install_ntp
install_supervisord
install_virtualenv
fix_python_dist_permissions
suppress_sshd_banner
suppress_debian_login_reminder
delete_default_account
create_pscu_account
create_pscu_venv
clone_odin_lpdpower
install_odin_lpdpower
set_pscu_splashscreen
install_pscu_startup
set_rootfs_readonly

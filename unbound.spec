%if 0%{?rhel} >= 7
%bcond_without systemd
%else
%bcond_with systemd
%endif

%{?!with_python:      %global with_python      1}
%{?!with_munin:       %global with_munin       0}
%{?!with_test:        %global with_test        0}

%if %{with_python}
%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}
%{!?python_sitearch: %global python_sitearch %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib(1)")}
%endif

%global _hardened_build 1

Summary: Validating, recursive, and caching DNS(SEC) resolver
Name: unbound
Version: 1.10.1
Release: 1%{?dist}
License: BSD
Url: https://unbound.net/
Source: https://www.unbound.net/downloads/%{name}-%{version}.tar.gz
Source1: unbound.service
Source2: unbound.conf
Source3: unbound.munin
Source4: unbound_munin_
Source5: root.key
Source6: dlv.isc.org.key
Source7: unbound-keygen.service
Source8: tmpfiles-unbound.conf
Source9: example.com.key
Source10: example.com.conf
Source11: block-example.com.conf
Source12: https://data.iana.org/root-anchors/icannbundle.pem
Source13: root.anchor
Source14: unbound.sysconfig
Source15: unbound-anchor.timer
Source16: unbound-munin.README
Source17: unbound-anchor.service
Source18: unbound.cron
Source19: unbound.init

Group: System Environment/Daemons
BuildRequires: openssl-devel
%if %{with_test}
# needed for the test suite
BuildRequires: bind-utils
BuildRequires: ldns
BuildRequires: vim-common nmap-ncat
%endif
# needed to regenerate configparser
BuildRequires: flex, byacc
BuildRequires: libevent-devel expat-devel
BuildRequires: pkgconfig
%if %{with_python}
BuildRequires:  python-devel swig
%endif
%{?with_systemd:BuildRequires: systemd-units}
# Required for SVN versions
# BuildRequires: bison

%if %{with systemd}
Requires(preun): systemd
Requires(postun): systemd
Requires(post): systemd
%else
Requires: initscripts >= 8.36
Requires(post): chkconfig
%endif

Requires(pre): shadow-utils
# Needed because /usr/sbin/unbound links unbound libs staticly
Requires: %{name}-libs%{?_isa} = %{version}-%{release}

%description
Unbound is a validating, recursive, and caching DNS(SEC) resolver.

The C implementation of Unbound is developed and maintained by NLnet
Labs. It is based on ideas and algorithms taken from a java prototype
developed by Verisign labs, Nominet, Kirei and ep.net.

Unbound is designed as a set of modular components, so that also
DNSSEC (secure DNS) validation and stub-resolvers (that do not run
as a server, but are linked into an application) are easily possible.

%if %{with_munin}
%package munin
Summary: Plugin for the munin / munin-node monitoring package
Group:     System Environment/Daemons
Requires: munin-node
Requires: %{name} = %{version}-%{release}, bc
BuildArch: noarch

%description munin
Plugin for the munin / munin-node monitoring package
%endif

%package devel
Summary: Development package that includes the unbound header files
Group: Development/Libraries
Requires: %{name}-libs%{?_isa} = %{version}-%{release}, openssl-devel
Requires: pkgconfig

%description devel
The devel package contains the unbound library and the include files

%package libs
Summary: Libraries used by the unbound server and client applications
Group: Applications/System
Requires(post): /sbin/ldconfig
Requires(post): grep
Requires(post): util-linux
Requires(post): sed
Requires(postun): /sbin/ldconfig
Requires: openssl >= 0.9.8g-12
%if %{with systemd}
Requires(preun): systemd
Requires(postun): systemd
Requires(post): systemd
%else
Requires: initscripts >= 8.36
Requires(post): chkconfig
%endif


%description libs
Contains libraries used by the unbound server and client applications

%if %{with_python}
%package python
Summary: Python modules and extensions for unbound
Group: Applications/System
Requires: %{name}-libs%{?_isa} = %{version}-%{release}

%description python
Python modules and extensions for unbound
%endif

%prep
%setup -q 

# regrnerate config parser due to new options added
echo "#include \"config.h\"" > util/configlexer.c || echo "Failed to create configlexer"
echo "#include \"util/configyyrename.h\"" >> util/configlexer.c || echo "Failed to create configlexer"
flex -i -t util/configlexer.lex >> util/configlexer.c  || echo "Failed to create configlexer"
yacc -y -d -o util/configparser.c util/configparser.y || echo "Failed to create configparser"

%build
%configure  --with-libevent --with-pthreads --with-ssl \
            --disable-rpath --disable-static \
            --enable-subnet --enable-ipsecmod \
            --with-conf-file=%{_sysconfdir}/%{name}/unbound.conf \
            --with-pidfile=%{_localstatedir}/run/%{name}/%{name}.pid \
%if %{with_python}
            --with-pythonmodule --with-pyunbound \
%endif
            --enable-sha2 --disable-gost --enable-ecdsa \
            --with-rootkey-file=%{_sharedstatedir}/unbound/root.key

%{__make} %{?_smp_mflags}
%{__make} %{?_smp_mflags} streamtcp

%install
%{__make} DESTDIR=%{buildroot} install
%{__make} DESTDIR=%{buildroot} unbound-event-install
install -d 0755 %{buildroot}%{_sysconfdir}/sysconfig
%if %{with systemd}
install -d 0755 %{buildroot}%{_unitdir} %{buildroot}%{_sysconfdir}/sysconfig
install -p -m 0644 %{SOURCE1} %{buildroot}%{_unitdir}/unbound.service
install -p -m 0644 %{SOURCE7} %{buildroot}%{_unitdir}/unbound-keygen.service
install -p -m 0644 %{SOURCE15} %{buildroot}%{_unitdir}/unbound-anchor.timer
install -p -m 0644 %{SOURCE17} %{buildroot}%{_unitdir}/unbound-anchor.service
%else
install -d 0755 %{buildroot}%{_initddir}/sysconfig %{buildroot}%{_sysconfdir}/cron.d
install -p -m 0644 %{SOURCE19} %{buildroot}%{_initddir}/unbound
install -p -m 0600 %{SOURCE18} %{buildroot}%{_sysconfdir}/cron.d/unbound-anchor
%endif

install -p -m 0755 %{SOURCE2} %{buildroot}%{_sysconfdir}/unbound
install -p -m 0644 %{SOURCE12} %{buildroot}%{_sysconfdir}/unbound
install -p -m 0644 %{SOURCE14} %{buildroot}%{_sysconfdir}/sysconfig/unbound
install -p -m 0644 %{SOURCE16} .
%if %{with_munin}
# Install munin plugin and its softlinks
install -d -m 0755 %{buildroot}%{_sysconfdir}/munin/plugin-conf.d
install -p -m 0644 %{SOURCE3} %{buildroot}%{_sysconfdir}/munin/plugin-conf.d/unbound
install -d -m 0755 %{buildroot}%{_datadir}/munin/plugins/
install -p -m 0755 %{SOURCE4} %{buildroot}%{_datadir}/munin/plugins/unbound
for plugin in unbound_munin_hits unbound_munin_queue unbound_munin_memory unbound_munin_by_type unbound_munin_by_class unbound_munin_by_opcode unbound_munin_by_rcode unbound_munin_by_flags unbound_munin_histogram; do
    ln -s unbound %{buildroot}%{_datadir}/munin/plugins/$plugin
done
%endif

# install streamtcp used for monitoring / debugging unbound's port 80/443 modes
install -m 0755 streamtcp %{buildroot}%{_sbindir}/unbound-streamtcp
# install streamtcp man page
install -m 0644 testcode/streamtcp.1 %{buildroot}/%{_mandir}/man1/unbound-streamtcp.1

install -D -m 0644 contrib/libunbound.pc %{buildroot}/%{_libdir}/pkgconfig/libunbound.pc


%if %{with systemd}
# Install tmpfiles.d config
install -d -m 0755 %{buildroot}%{_tmpfilesdir} %{buildroot}%{_sharedstatedir}/unbound
install -m 0644 %{SOURCE8} %{buildroot}%{_tmpfilesdir}/unbound.conf
%endif

# Install shared state dir
install -d -m 0755 %{buildroot}%{_sharedstatedir}/unbound

# install root and DLV key - we keep a copy of the root key in old location,
# in case user has changed the configuration and we wouldn't update it there
install -m 0644 %{SOURCE5} %{SOURCE6} %{buildroot}%{_sysconfdir}/unbound/
install -m 0644 %{SOURCE13} %{buildroot}%{_sharedstatedir}/unbound/root.key

# remove static library from install (fedora packaging guidelines)
rm %{buildroot}%{_libdir}/*.la
%if %{with_python}
rm %{buildroot}%{python_sitearch}/*.la
%endif

# create softlink for all functions of libunbound man pages
for mpage in ub_ctx ub_result ub_ctx_create ub_ctx_delete ub_ctx_set_option ub_ctx_get_option ub_ctx_config ub_ctx_set_fwd ub_ctx_resolvconf ub_ctx_hosts ub_ctx_add_ta ub_ctx_add_ta_file ub_ctx_trustedkeys ub_ctx_debugout ub_ctx_debuglevel ub_ctx_async ub_poll ub_wait ub_fd ub_process ub_resolve ub_resolve_async ub_cancel ub_resolve_free ub_strerror ub_ctx_print_local_zones ub_ctx_zone_add ub_ctx_zone_remove ub_ctx_data_add ub_ctx_data_remove;
do
  echo ".so man3/libunbound.3" > %{buildroot}%{_mandir}/man3/$mpage ;
done

mkdir -p %{buildroot}%{_localstatedir}/run/unbound

# Install directories for easier config file drop in

mkdir -p %{buildroot}%{_sysconfdir}/unbound/{keys.d,conf.d,local.d}
install -p %{SOURCE9} %{buildroot}%{_sysconfdir}/unbound/keys.d/
install -p %{SOURCE10} %{buildroot}%{_sysconfdir}/unbound/conf.d/
install -p %{SOURCE11} %{buildroot}%{_sysconfdir}/unbound/local.d/

# Link unbound-control-setup.8 manpage to unbound-control.8
echo ".so man8/unbound-control.8" > %{buildroot}/%{_mandir}/man8/unbound-control-setup.8

%files 
%doc doc/README doc/CREDITS doc/LICENSE doc/FEATURES
%if %{with systemd}
%{_unitdir}/%{name}.service
%{_unitdir}/%{name}-keygen.service
%attr(0644,root,root) %{_tmpfilesdir}/unbound.conf
%else
%attr(0755,root,root) %{_initddir}/%{name}
%attr(0755,root,root) %{_sysconfdir}/cron.d/%{name}-anchor
%endif
%attr(0755,unbound,unbound) %dir %{_localstatedir}/run/%{name}
%attr(0644,root,root) %config(noreplace) %{_sysconfdir}/%{name}/unbound.conf
%attr(0644,root,root) %config(noreplace) %{_sysconfdir}/sysconfig/%{name}
%dir %attr(0755,root,unbound) %{_sysconfdir}/%{name}/keys.d
%attr(0664,root,unbound) %config(noreplace) %{_sysconfdir}/%{name}/keys.d/*.key
%dir %attr(0755,root,unbound) %{_sysconfdir}/%{name}/conf.d
%attr(0664,root,unbound) %config(noreplace) %{_sysconfdir}/%{name}/conf.d/*.conf
%dir %attr(0755,root,unbound) %{_sysconfdir}/%{name}/local.d
%attr(0664,root,unbound) %config(noreplace) %{_sysconfdir}/%{name}/local.d/*.conf
%{_sbindir}/unbound
%{_sbindir}/unbound-checkconf
%{_sbindir}/unbound-control
%{_sbindir}/unbound-control-setup
%{_sbindir}/unbound-host
%{_sbindir}/unbound-streamtcp
%{_mandir}/man1/*
%{_mandir}/man5/*
%{_mandir}/man8/*

%if %{with_python}
%files python
%{python_sitearch}/*
%doc libunbound/python/examples/*
%doc pythonmod/examples/*
%endif

%if %{with_munin}
%files munin
%config(noreplace) %{_sysconfdir}/munin/plugin-conf.d/unbound
%{_datadir}/munin/plugins/unbound*
%doc unbound-munin.README
%endif

%files devel
%{_libdir}/libunbound.so
%{_includedir}/unbound.h
%{_includedir}/unbound-event.h
%{_mandir}/man3/*
%doc README
%{_libdir}/pkgconfig/*.pc

%files libs
%attr(0755,root,root) %dir %{_sysconfdir}/%{name}
%{_sbindir}/unbound-anchor
%{_libdir}/libunbound.so.*
%{_sysconfdir}/%{name}/icannbundle.pem
%if %{with systemd}
%{_unitdir}/unbound-anchor.timer
%{_unitdir}/unbound-anchor.service
%else
%attr(0644,root,root) %{_sysconfdir}/cron.d/unbound-anchor
%endif
%dir %attr(0755,unbound,unbound) %{_sharedstatedir}/%{name}
# this file will be modified always after installation
%attr(0644,unbound,unbound) %config(noreplace) %{_sharedstatedir}/%{name}/root.key
%attr(0644,root,root) %config(noreplace) %{_sysconfdir}/%{name}/dlv.isc.org.key
# just left for backwards compat with user changed unbound.conf files - format is different!
%attr(0644,root,root) %config(noreplace) %{_sysconfdir}/%{name}/root.key
%doc doc/README doc/LICENSE

%pre libs
getent group unbound >/dev/null || groupadd -r unbound
getent passwd unbound >/dev/null || \
useradd -r -g unbound -d %{_sysconfdir}/unbound -s /sbin/nologin \
-c "Unbound DNS resolver" unbound
exit 0

%post
%if %{with systemd}
%systemd_post unbound.service
%systemd_post unbound-keygen.service
%else
/sbin/chkconfig --add %{name}
%endif

%post libs 
/sbin/ldconfig
# If update contains new keys not already in database, use package keys
if [ "$1" -eq 2 -a -f %{_sharedstatedir}/unbound/root.key.rpmnew ]; then
        runuser --command="
	cp -pf %{_sharedstatedir}/unbound/root.key %{_sharedstatedir}/unbound/root.key.rpmupdate && \
	sed -e 's/;.*//' -e '/^[[:space:]]*$/ d' %{_sharedstatedir}/unbound/root.key.rpmnew | while read KEY;
	do
		if ! grep -q \"\$KEY\" %{_sharedstatedir}/unbound/root.key.rpmupdate; then
			echo \"\$KEY\" >> %{_sharedstatedir}/unbound/root.key.rpmupdate || exit 1;
		fi;
	done && \
	mv %{_sharedstatedir}/unbound/root.key.rpmupdate %{_sharedstatedir}/unbound/root.key" --shell /bin/sh unbound || :
fi
runuser  --command="%{_sbindir}/unbound-anchor -a %{_sharedstatedir}/unbound/root.key -c %{_sysconfdir}/unbound/icannbundle.pem"  --shell /bin/sh unbound ||:
%if %{with systemd}
%systemd_post unbound-anchor.timer
# the Unit is in presets, but would be started afte reboot
/bin/systemctl start unbound-anchor.timer >/dev/null 2>&1 || :
%endif

%preun
%if %{with systemd}
%systemd_preun unbound.service
%systemd_preun unbound-keygen.service
%else
if [ "$1" -eq 0 ]; then
        /sbin/service %{name} stop >/dev/null 2>&1
        /sbin/chkconfig --del %{name}
fi
%endif

%preun libs
%if %{with systemd}
%systemd_preun unbound-anchor.timer
%endif

%postun 
%if %{with systemd}
%systemd_postun_with_restart unbound.service
%systemd_postun unbound-keygen.service
%else
if [ "$1" -ge "1" ]; then
  /sbin/service %{name} condrestart >/dev/null 2>&1 || :
fi
%endif

%postun libs
/sbin/ldconfig
%if %{with systemd}
%systemd_postun_with_restart unbound-anchor.timer
%endif

%triggerun -- unbound < 1.4.12-4
%if %{with systemd}
# Save the current service runlevel info
# User must manually run systemd-sysv-convert --apply unbound
# to migrate them to systemd targets
/usr/bin/systemd-sysv-convert --save unbound >/dev/null 2>&1 ||:

# Run these because the SysV package being removed won't do them
/sbin/chkconfig --del unbound >/dev/null 2>&1 || :
/bin/systemctl try-restart unbound.service >/dev/null 2>&1 || :
/bin/systemctl try-restart unbound-keygen.service >/dev/null 2>&1 || :
%endif


%check
%if %{with_test}
  make check
  make longcheck
%endif

%changelog
* Mon Jun 15 2020 Dave Rawks <dave@rawks.io> - 1.10.1-1
- initial IUS style specfile

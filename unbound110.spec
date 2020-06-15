%{?!with_python:      %global with_python      1}
%{?!with_munin:      %global with_munin      0}

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
Url: http://www.nlnetlabs.nl/unbound/
Source: http://www.unbound.net/downloads/%{name}-%{version}.tar.gz

Group: System Environment/Daemons
BuildRequires: flex, openssl-devel , ldns-devel >= 1.6.13
BuildRequires: libevent-devel expat-devel

%if %{with_python}
BuildRequires:  python-devel swig
%endif
# Required for SVN versions
# BuildRequires: bison

Requires(post): chkconfig
Requires(preun): chkconfig
Requires(preun): initscripts
Requires(postun): initscripts
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

%package devel
Summary: Development package that includes the unbound header files
Group: Development/Libraries
Requires: %{name}-libs%{?_isa} = %{version}-%{release}, openssl-devel, ldns-devel

%description devel
The devel package contains the unbound library and the include files

%package libs
Summary: Libraries used by the unbound server and client applications
Group: Applications/System
Requires(post): /sbin/ldconfig
Requires(post): coreutils
Requires(post): grep
Requires(post): sed
Requires(postun): /sbin/ldconfig
Requires: openssl
Requires: crontabs

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

%build
%configure  --with-ldns --with-libevent --with-pthreads --with-ssl \
            --disable-rpath --disable-static \
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
rm -rf %{buildroot}
%{__make} DESTDIR=%{buildroot} install
install -d 0755 %{buildroot}%{_initrddir} %{buildroot}%{_sysconfdir}/sysconfig
install -p -m 0755 %{SOURCE1} %{buildroot}%{_initrddir}/unbound
install -p -m 0755 %{SOURCE2} %{buildroot}%{_sysconfdir}/unbound
install -p -m 0644 %{SOURCE12} %{buildroot}%{_sysconfdir}/unbound
install -p -m 0644 %{SOURCE14}  %{buildroot}%{_sysconfdir}/sysconfig/unbound
install -d -m 0755 %{buildroot}%{_sysconfdir}/cron.d %{buildroot}%{_sharedstatedir}/unbound
install -p -m 0755 %{SOURCE15}   %{buildroot}%{_sysconfdir}/cron.d/unbound-anchor

# install streamtcp used for monitoring / debugging unbound's port 80/443 modes
install -m 0755 streamtcp %{buildroot}%{_sbindir}/unbound-streamtcp
# install streamtcp man page
install -m 0644 testcode/streamtcp.1 %{buildroot}/%{_mandir}/man1/unbound-streamtcp.1

# install root and DLV key - we keep a copy of the root key in old location,
install -m 0644 %{SOURCE5} %{SOURCE6} %{buildroot}%{_sysconfdir}/unbound/
install -m 0644 %{SOURCE13} %{buildroot}%{_sharedstatedir}/unbound/root.key

# remove static library from install (fedora packaging guidelines)
rm -f %{buildroot}%{_libdir}/*.la
%if %{with_python}
rm -f %{buildroot}%{python_sitearch}/*.la
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

%if %{with_munin}
install -p -m 0644 %{SOURCE16}  .
%endif

%files
%doc doc/README doc/CREDITS doc/LICENSE doc/FEATURES
%attr(0755,root,root) %{_initrddir}/%{name}
%attr(0755,root,root) %dir %{_sysconfdir}/%{name}
%ghost %attr(0755,unbound,unbound) %dir %{_localstatedir}/run/%{name}
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

%files devel
%{_libdir}/libunbound.so
%{_includedir}/unbound.h
%{_mandir}/man3/*
%doc README

%files libs
%attr(0755,root,root) %dir %{_sysconfdir}/%{name}
%{_sbindir}/unbound-anchor
%{_libdir}/libunbound.so.*
%{_sysconfdir}/%{name}/icannbundle.pem
%attr(0644,root,root) %{_sysconfdir}/cron.d/unbound-anchor
%attr(0755,unbound,unbound) %dir %{_sharedstatedir}/%{name}
# this file will be modified always after installation
%attr(0644,unbound,unbound) %config(noreplace) %{_sharedstatedir}/%{name}/root.key
%attr(0644,root,root) %config(noreplace) %{_sysconfdir}/%{name}/root.key
%attr(0644,root,root) %config(noreplace) %{_sysconfdir}/%{name}/dlv.isc.org.key
%doc doc/README doc/LICENSE

%pre libs
getent group unbound >/dev/null || groupadd -r unbound
getent passwd unbound >/dev/null || \
useradd -r -g unbound -d %{_sysconfdir}/unbound -s /sbin/nologin \
-c "Unbound DNS resolver" unbound || exit 0

%post
/sbin/chkconfig --add %{name}

%post libs
/sbin/ldconfig
# If update contains new keys not already in database, use package keys
if [ "$1" -eq 2 -a -f %{_sharedstatedir}/unbound/root.key.rpmnew ]; then
        /sbin/runuser --command="
	cp -pf %{_sharedstatedir}/unbound/root.key %{_sharedstatedir}/unbound/root.key.rpmupdate && \
	sed -e 's/;.*//' -e '/^[[:space:]]*$/ d' %{_sharedstatedir}/unbound/root.key.rpmnew | while read KEY;
	do
		if ! grep -q \"\$KEY\" %{_sharedstatedir}/unbound/root.key.rpmupdate; then
			echo \"\$KEY\" >> %{_sharedstatedir}/unbound/root.key.rpmupdate || exit 1;
		fi;
	done && \
	mv %{_sharedstatedir}/unbound/root.key.rpmupdate %{_sharedstatedir}/unbound/root.key" --shell /bin/sh unbound || :
fi
/sbin/runuser --command="%{_sbindir}/unbound-anchor -a %{_sharedstatedir}/unbound/root.key -c %{_sysconfdir}/unbound/icannbundle.pem"  --shell /bin/sh unbound || exit 0

%preun
if [ "$1" -eq 0 ]; then
        /sbin/service %{name} stop >/dev/null 2>&1
        /sbin/chkconfig --del %{name}
fi

%postun
if [ "$1" -ge "1" ]; then
  /sbin/service %{name} condrestart >/dev/null 2>&1 || :
fi

%postun libs -p /sbin/ldconfig

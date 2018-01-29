%{?_javapackages_macros:%_javapackages_macros}

Name:           gluegen2
Version:        2.3.2
Release:        7.1
%global src_name gluegen-v%{version}
Summary:        Java/JNI glue code generator to call out to ANSI C

Group:          Development/Java
License:        BSD
URL:            http://jogamp.org/
Source0:        http://jogamp.org/deployment/v%{version}/archive/Sources/%{src_name}.tar.xz
Source1:        http://jogamp.org/deployment/v%{version}/archive/Sources/jcpp-v%{version}.tar.xz
Patch1:         %{name}-0001-renamed-library.patch
# gluegen2.spec: W: patch-not-applied Patch2: 0002-use-fedora-jni.patch
#                Applied with %%{_libdir} and %%{name} resolved
Patch2:         %{name}-0002-use-fedora-jni.patch
Patch3:         %{name}-0003-disable-executable-tmp-tests.patch
Patch4:         %{name}-0004-add-antlr-jar-to-all-targets.patch
Patch5:         %{name}-0005-use-system-antlib.patch
Patch6:         %{name}-0006-disable-static-libgcc.patch
Patch7:         %{name}-0007-add-ppc64-aarch64.patch
Patch8:         %{name}-0008-jcpp-remove-javax-api.patch

BuildRequires:  java-devel
BuildRequires:  jpackage-utils
BuildRequires:  ant-antlr
BuildRequires:  ant-contrib
BuildRequires:  ant-junit
BuildRequires:  cpptasks
BuildRequires:  maven-local

Requires:       java-headless
Requires:       jpackage-utils

%description
GlueGen is a tool which automatically generates the Java and JNI
code necessary to call C libraries. It reads as input ANSI C header
files and separate configuration files which provide control over
many aspects of the glue code generation. GlueGen uses a complete
ANSI C parser and an internal representation (IR) capable of
representing all C types to represent the APIs for which it
generates interfaces.

%package devel
Summary:        GlueGen2 devel utilities required to build JOGL2
Group:          Development/Java
BuildArch:      noarch

Requires:       %{name} = %{version}-%{release}
Requires:       ant-antlr
Requires:       ant-contrib
Requires:       ant-junit
Requires:       cpptasks

%description devel
GlueGen devel utilities provide some ant targets and shared files to build
application.

%package javadoc
Summary:        Javadoc for GlueGen2
Group:          Development/Java
BuildArch:      noarch

%description javadoc
Javadoc for GlueGen2.

%package doc
Summary:        GlueGen's user manual
Group:          Development/Java
BuildArch:      noarch

%description doc
GlueGen's user manual.

%prep
%setup -n %{src_name}
tar -xJf %{SOURCE1} -C jcpp --strip 1

%patch1 -p1
sed -e "s|%%{_libdir}|%{_libdir}|;s|%%{name}|%{name}|" %{PATCH2} \
    >use-fedora-jni.patch
/usr/bin/patch -s -p1 --fuzz=0 <use-fedora-jni.patch
%patch3 -p1
%patch4 -p1
%patch5 -p1
%patch6 -p1
%patch7 -p1
%patch8 -p1

# Remove bundled dependencies
find -name "*.jar" -type f -exec rm {} \;
find -name "*.apk" -type f -exec rm {} \;
rm -fr make/lib

# Fix wrong-script-end-of-line-encoding
rm make/scripts/*.bat

# Fix spurious-executable-perm
chmod -x LICENSE.txt
chmod -x doc/manual/index.html
chmod -x src/native/*/*
find src/java/ -type f -exec chmod -x {} +
find make/scripts -type f -not -name "*.sh" -exec chmod -x {} +

# Fix non-executable-script
find make/scripts -type f -name "*.sh" -exec chmod +x {} +

# Fix script-without-shebang
find make/scripts -type f -name "*.sh" -exec sed -i -e '1i#!/bin/sh' {} +

# Remove hardcoded classpath
sed -i '/Class-Path/I d' make/Manifest

# git executable should not be used, use true (to avoid checkout) instead
sed -i 's/executable="git"/executable="true"/' make/build.xml

# 7z executable is not provided, use true (to avoid archive) instead
sed -i 's/executable="7z"/executable="true"/' make/jogamp-archivetasks.xml

# mvn executable should not be used, use true (to avoid install) instead
sed -i 's/executable="mvn"/executable="true"/' make/build.xml

%build

# Clean up some tests
rm -f src/junit/com/jogamp/common/util/TestVersionSemantics.java src/junit/com/jogamp/junit/util/VersionSemanticsUtil.java

cd make
xargs -t ant <<EOF
 -verbose
 -Dc.compiler.debug=true
 -Djavacdebug=false
%ifarch x86_64
 -Djavac.memorymax=1024m
%else
 -Djavac.memorymax=256m
%endif

 -Dantlr.jar=%{_javadir}/antlr.jar
 -Djunit.jar=%{_javadir}/junit.jar
 -Dant.jar=%{_javadir}/ant.jar
 -Dant-junit.jar=%{_javadir}/ant/ant-junit.jar

 -Djavadoc.link=%{_javadocdir}/java

 all
 javadoc
 maven.install
EOF

%install
mkdir -p %{buildroot}%{_javadir}/%{name} \
    %{buildroot}%{_libdir}/%{name} \
    %{buildroot}%{_jnidir}

install build/gluegen.jar %{buildroot}%{_javadir}/%{name}.jar
install build/gluegen-rt.jar %{buildroot}%{_jnidir}/%{name}-rt.jar
ln -s ../../..%{_jnidir}/%{name}-rt.jar %{buildroot}%{_libdir}/%{name}/
install build/obj/libgluegen-rt.so %{buildroot}%{_libdir}/%{name}/lib%{name}-rt.so

# Provide JPP pom
mkdir -p %{buildroot}%{_mavenpomdir}
install -pm 644 build/pom-gluegen.xml %{buildroot}%{_mavenpomdir}/JPP-%{name}.pom
install -pm 644 build/pom-gluegen-rt.xml %{buildroot}%{_mavenpomdir}/JPP-%{name}-rt.pom
%add_maven_depmap JPP-%{name}.pom %{name}.jar
%add_maven_depmap JPP-%{name}-rt.pom %{name}-rt.jar

# Make the devel package. This package is needed to build JOGL2
%global gluegen_devel_dir %{_datadir}/gluegen2
%global inst_srcdir %{buildroot}%{gluegen_devel_dir}
mkdir -p %{inst_srcdir} %{inst_srcdir}/build
cp -rdf -t %{inst_srcdir} make
cp build/artifact.properties %{inst_srcdir}/build/artifact.properties

# Make the javadoc package
mkdir -p %{buildroot}%{_javadocdir}/%{name}
cp -rdf build/javadoc/gluegen/javadoc/* %{buildroot}%{_javadocdir}/%{name}

# Make the doc package
mkdir -p %{buildroot}%{_docdir}/%{name}
cp -rdf doc/manual/* %{buildroot}%{_docdir}/%{name}
cp LICENSE.txt %{buildroot}%{_docdir}/%{name}/
cp LICENSE.txt %{buildroot}%{_javadocdir}/%{name}/

%check
cd make
_JAVA_OPTIONS="-Djogamp.debug=true -Djava.library.path=../build/test/build/natives" xargs -t ant <<EOF
 -verbose
 -Djavacdebug=true
 -Dc.compiler.debug=true
 -Djavacdebuglevel=lines,vars,source
 -Dcommon.gluegen.build.done=true

 -Dantlr.jar=%{_javadir}/antlr.jar
 -Djunit.jar=%{_javadir}/junit.jar
 -Dant.jar=%{_javadir}/ant.jar
 -Dant-junit.jar=%{_javadir}/ant/ant-junit.jar
 -Dgluegen.jar=%{buildroot}%{_javadir}/%{name}.jar
 -Dgluegen-rt.jar=%{buildroot}%{_libdir}/%{name}/%{name}-rt.jar
 -Dswt.jar=%{_libdir}/eclipse/swt.jar

 junit.run
EOF

rm -fr %{buildroot}%{_jnidir}/test

%files
%{_docdir}/%{name}/LICENSE.txt
%{_jnidir}/%{name}-rt.jar
%{_libdir}/%{name}
%{_mavenpomdir}/JPP-%{name}-rt.pom

%files devel
%{_docdir}/%{name}/LICENSE.txt
%{_javadir}/%{name}.jar
%{_mavenpomdir}/JPP-%{name}.pom
%{_datadir}/maven-metadata/%{name}.xml
%{gluegen_devel_dir}

%files javadoc
%{_javadocdir}/%{name}

%files doc
%{_docdir}/%{name}

%changelog
* Wed Aug 02 2017 Fedora Release Engineering <releng@fedoraproject.org> - 2.3.2-7
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Binutils_Mass_Rebuild

* Wed Jul 26 2017 Fedora Release Engineering <releng@fedoraproject.org> - 2.3.2-6
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Mass_Rebuild

* Fri Feb 10 2017 Fedora Release Engineering <releng@fedoraproject.org> - 2.3.2-5
- Rebuilt for https://fedoraproject.org/wiki/Fedora_26_Mass_Rebuild

* Wed Feb 03 2016 Fedora Release Engineering <releng@fedoraproject.org> - 2.3.2-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_24_Mass_Rebuild

* Fri Dec 04 2015 Marcin Juszkiewicz <mjuszkiewicz@redhat.com> - 2.3.2-3
- Update secondary archs patch to build jogl2 on aarch64.

* Wed Dec 02 2015 Clément David <c.david86@gmail.com> - 2.3.2-2
- Preserve the shipped OpenGL API

* Tue Dec 01 2015 Clément David <c.david86@gmail.com> - 2.3.2-1
- Update version

* Thu Nov 26 2015 Dan Horák <dan[at]danny.cz> - 2.2.4-4
- fix build on ppc arches (#1267269)

* Wed Jun 17 2015 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.2.4-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_23_Mass_Rebuild

* Wed Feb 18 2015 Peter Robinson <pbrobinson@fedoraproject.org> 2.2.4-2
- Add support for aarch64/ppc64

* Tue Sep 09 2014 Clément David <c.david86@gmail.com> - 2.2.4-1
- Update version
- Disable the use of static-libgcc
- Enable ant verbose build to trace native compilation calls

* Sat Aug 16 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.0.2-5
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_22_Mass_Rebuild

* Sat Jun 07 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.0.2-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_Mass_Rebuild

* Thu Feb 27 2014 Clément David <c.david86@gmail.com> - 2.0.2-3
- Change R:java to R:java-headless (Bug 1068109).

* Tue Jan 07 2014 Clément David <c.david86@gmail.com> - 2.0.2-2
- Fix bug #1001254 about docdir issue
- Allow the user to install javadoc without the main package

* Mon Sep 09 2013 Clément David <c.david86@gmail.com> - 2.0.2-1
- Update to the stable 2.0.2 version

* Tue Aug 20 2013 Clément David <c.david86@gmail.com> - 2.0-0.11.rc12
- Fix the build for armv7hl with only configuration
- log the ant arguments to stderr

* Fri Aug 02 2013 Clément David <c.david86@gmail.com> - 2.0-0.10.rc12
- Fix the build for armv7hl

* Wed Jul 10 2013 Clément David <c.david86@gmail.com> - 2.0-0.9.rc12
- Update to rc12

* Wed Feb 06 2013 Java SIG <java-devel@lists.fedoraproject.org> - 2.0-0.8.rc11
- Update for https://fedoraproject.org/wiki/Fedora_19_Maven_Rebuild
- Replace maven BuildRequires with maven-local

* Fri Jan 25 2013 Clément David <c.david86@gmail.com> - 2.0-0.7.rc11
- Upgrade to the Java packaging draft (JNI jar/so location)

* Thu Jan 03 2013 Clément David <c.david86@gmail.com> - 2.0-0.6.rc11
- Update version

* Wed Dec 19 2012 Stanislav Ochotnicky <sochotnicky@redhat.com> - 2.0-0.5.rc10.1
- revbump after jnidir change
- Fix symlink for JNI jar

* Mon Oct 01 2012 Clément David <c.david86@gmail.com> - 2.0-0.4.rc10
- Prefix patches with package name
- Use /usr/share/gluegen2 devel files

* Thu Sep 27 2012 Clément David <c.david86@gmail.com> - 2.0-0.3.rc10
- Patch to use System.load(..)
- Use devel subpackage for gluegen2 ant task

* Thu Sep 20 2012 Clément David <c.david86@gmail.com> - 2.0-0.2.rc10
- Add javadoc subpackage
- Provide maven pom files

* Mon Sep 10 2012 Clément David <c.david86@gmail.com> - 2.0-0.1.rc10
- Initial package with inspiration on gluegen spec


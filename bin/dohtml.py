#!@PREFIX_PORTAGE_PYTHON@
# Copyright 1999-2006 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2

#
# Typical usage:
# dohtml -r docs/*
#  - put all files and directories in docs into /usr/share/doc/${PF}/html
# dohtml foo.html
#  - put foo.html into /usr/share/doc/${PF}/html
#
#
# Detailed usage:
# dohtml <list-of-files> 
#  - will install the files in the list of files (space-separated list) into 
#    /usr/share/doc/${PF}/html, provided the file ends in .htm, .html, .css,
#      .js, ,gif, .jpeg, .jpg, or .png.
# dohtml -r <list-of-files-and-directories>
#  - will do as 'dohtml', but recurse into all directories, as long as the 
#    directory name is not CVS
# dohtml -A jpe,java [-r] <list-of-files[-and-directories]>
#  - will do as 'dohtml' but add .jpe,.java (default filter list is
#    added to your list)
# dohtml -a png,gif,html,htm [-r] <list-of-files[-and-directories]>
#  - will do as 'dohtml' but filter on .png,.gif,.html,.htm (default filter 
#    list is ignored)
# dohtml -x CVS,SCCS,RCS -r <list-of-files-and-directories>
#  - will do as 'dohtml -r', but ignore directories named CVS, SCCS, RCS
#

from __future__ import print_function

import os
import sys

def dodir(path):
	os.spawnlp(os.P_WAIT, "install", "install", "-d", path)

def dofile(src,dst):
	os.spawnlp(os.P_WAIT, "install", "install", "-m0644", src, dst)

def eqawarn(lines):
	cmd = "source '%s/isolated-functions.sh' ; " % \
		os.environ["PORTAGE_BIN_PATH"]
	for line in lines:
		cmd += "eqawarn \"%s\" ; " % line
	os.spawnlp(os.P_WAIT, "bash", "bash", "-c", cmd)

skipped_directories = []

def install(basename, dirname, options, prefix=""):
	fullpath = basename
	if prefix:
		fullpath = prefix + "/" + fullpath
	if dirname:
		fullpath = dirname + "/" + fullpath

	if options.DOCDESTTREE:
		destdir = options.ED + "usr/share/doc/" + options.PF + "/" + options.DOCDESTTREE + "/" + options.doc_prefix + "/" + prefix
	else:
		destdir = options.ED + "usr/share/doc/" + options.PF + "/html/" + options.doc_prefix + "/" + prefix

	if not os.path.exists(fullpath):
		sys.stderr.write("!!! dohtml: %s does not exist\n" % fullpath)
		return False
	elif os.path.isfile(fullpath):
		ext = os.path.splitext(basename)[1]
		if (len(ext) and ext[1:] in options.allowed_exts) or basename in options.allowed_files:
			dodir(destdir)
			dofile(fullpath, destdir + "/" + basename)
	elif options.recurse and os.path.isdir(fullpath) and \
	     basename not in options.disallowed_dirs:
		for i in os.listdir(fullpath):
			pfx = basename
			if prefix: pfx = prefix + "/" + pfx
			install(i, dirname, options, pfx)
	elif not options.recurse and os.path.isdir(fullpath):
		global skipped_directories
		skipped_directories.append(fullpath)
		return False
	else:
		return False
	return True


class OptionsClass:
	def __init__(self):
		self.PF = ""
		self.ED = ""
		self.DOCDESTTREE = ""
		
		if "PF" in os.environ:
			self.PF = os.environ["PF"]
		if "force-prefix" not in os.environ.get("FEATURES", "").split() and \
			os.environ.get("EAPI", "0") in ("0", "1", "2"):
			self.ED = os.environ.get("D", "")
		else:
			self.ED = os.environ.get("ED", "")
		if "_E_DOCDESTTREE_" in os.environ:
			self.DOCDESTTREE = os.environ["_E_DOCDESTTREE_"]
		
		self.allowed_exts = [ 'htm', 'html', 'css', 'js',
			'gif', 'jpeg', 'jpg', 'png' ]
		self.allowed_files = []
		self.disallowed_dirs = [ 'CVS' ]
		self.recurse = False
		self.verbose = False
		self.doc_prefix = ""

def print_help():
	opts = OptionsClass()

	print("dohtml [-a .foo,.bar] [-A .foo,.bar] [-f foo,bar] [-x foo,bar]")
	print("       [-r] [-V] <file> [file ...]")
	print()
	print(" -a   Set the list of allowed to those that are specified.")
	print("      Default:", ",".join(opts.allowed_exts))
	print(" -A   Extend the list of allowed file types.")
	print(" -f   Set list of allowed extensionless file names.")
	print(" -x   Set directories to be excluded from recursion.")
	print("      Default:", ",".join(opts.disallowed_dirs))
	print(" -p   Set a document prefix for installed files (empty by default).")
	print(" -r   Install files and directories recursively.")
	print(" -V   Be verbose.")
	print()

def parse_args():
	options = OptionsClass()
	args = []
	
	x = 1
	while x < len(sys.argv):
		arg = sys.argv[x]
		if arg in ["-h","-r","-V"]:
			if arg == "-h":
				print_help()
				sys.exit(0)
			elif arg == "-r":
				options.recurse = True
			elif arg == "-V":
				options.verbose = True
		elif sys.argv[x] in ["-A","-a","-f","-x","-p"]:
			x += 1
			if x == len(sys.argv):
				print_help()
				sys.exit(0)
			elif arg == "-p":
				options.doc_prefix = sys.argv[x]
			else:
				values = sys.argv[x].split(",")
				if arg == "-A":
					options.allowed_exts.extend(values)
				elif arg == "-a":
					options.allowed_exts = values
				elif arg == "-f":
					options.allowed_files = values
				elif arg == "-x":
					options.disallowed_dirs = values
		else:
			args.append(sys.argv[x])
		x += 1
	
	return (options, args)

def main():

	(options, args) = parse_args()

	if options.verbose:
		print("Allowed extensions:", options.allowed_exts)
		print("Document prefix : '" + options.doc_prefix	 + "'")
		print("Allowed files :", options.allowed_files)

	success = False
	
	for x in args:
		basename = os.path.basename(x)
		dirname  = os.path.dirname(x)
		success |= install(basename, dirname, options)

	global skipped_directories
	for x in skipped_directories:
		eqawarn(["QA Notice: dohtml on directory " + \
			"'%s' without recursion option" % x])

	if success:
		retcode = 0
	else:
		retcode = 1

	sys.exit(retcode)

if __name__ == "__main__":
	main()

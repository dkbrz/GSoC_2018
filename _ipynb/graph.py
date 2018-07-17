import sys
from tool.func import *
import argparse
import inspect

# top-level parser
parser = argparse.ArgumentParser()
subparsers = parser.add_subparsers()

parser_download = subparsers.add_parser('download')
parser_download.set_defaults(func=download)

parser_list = subparsers.add_parser('list')
parser_list.add_argument('path', type=str, action='store', nargs='?', default='./dictionaries/')
parser_list.set_defaults(func=list_files)

parser_preproc = subparsers.add_parser('preprocessing')
parser_preproc.set_defaults(func=preprocessing)

parser_configure = subparsers.add_parser('config')
parser_configure.add_argument('lang1', type=str, action='store')
parser_configure.add_argument('lang2', type=str, action='store')
parser_configure.set_defaults(func=get_relevant_languages)

parser_configure = subparsers.add_parser('load_file')
parser_configure.add_argument('lang1', type=str, action='store')
parser_configure.add_argument('lang2', type=str, action='store')
parser_configure.set_defaults(func=load_file)

parser_eval = subparsers.add_parser('eval')
parser_eval.add_argument('lang1', type=str, action='store')
parser_eval.add_argument('lang2', type=str, action='store')
parser_eval.add_argument('--n', type=int, action='store', nargs='?', default=10)
parser_eval.add_argument('--topn', type=int, action='store', nargs='?', default=None)
parser_eval.add_argument('--n_iter', type=int, action='store', nargs='?', default=3)
parser_eval.add_argument('--cutoff', type=int, action='store', nargs='?', default=4)
parser_eval.set_defaults(func=eval_loop)

parser_eval = subparsers.add_parser('preview')
parser_eval.add_argument('lang1', type=str, action='store')
parser_eval.add_argument('lang2', type=str, action='store')
parser_eval.add_argument('--topn', type=int, action='store', nargs='?', default=None)
parser_eval.add_argument('--cutoff', type=int, action='store', nargs='?', default=4)
parser_eval.set_defaults(func=get_translations)

parser_configure = subparsers.add_parser('convert')
parser_configure.add_argument('lang1', type=str, action='store')
parser_configure.add_argument('lang2', type=str, action='store')
parser_configure.set_defaults(func=convert_to_dix)

args = parser.parse_args()
arg_spec = inspect.getargspec(args.func)
if arg_spec.keywords:
    args_for_func = vars(args)
else:
    args_for_func = {k:getattr(args, k) for k in arg_spec.args}

args.func(**args_for_func)

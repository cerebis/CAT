#!/usr/bin/env python3

import argparse
import datetime
import decimal
import multiprocessing
import sys

import about
import check
import shared
import tax


def parse_arguments():
    parser = argparse.ArgumentParser(
            prog='CAT bin',
            description='Run Bin Annotation Tool (BAT) on a single bin.',
            usage='CAT bin -b -d -t [options] [-h / --help]',
            add_help=False)
    
    required = parser.add_argument_group('Required arguments')

    required.add_argument(
            '-b',
            '--bin_fasta',
            dest='bin_fasta',
            metavar='',
            required=True,
            type=str,
            action=shared.PathAction,
            help='Path to bin fasta file.')
    required.add_argument(
            '-d',
            '--database_folder',
            metavar='',
            required=True,
            type=str,
            action=shared.PathAction,
            help='Path to folder that contains database files.')
    required.add_argument(
            '-t',
            '--taxonomy_folder',
            dest='taxonomy_folder',
            metavar='',
            required=True,
            type=str,
            action=shared.PathAction,
            help='Path to folder that contains taxonomy files.')

    optional = parser.add_argument_group('Optional arguments')
    
    optional.add_argument(
            '-r',
            '--range',
            dest='r',
            metavar='',
            required=False,
            type=float,
            choices = [i for i in range(50)],
            action=shared.DecimalAction,
            default=decimal.Decimal(5),
            help='r parameter [0-49] (default: 5).')
    optional.add_argument(
            '-f',
            '--fraction',
            dest='f',
            metavar='',
            required=False,
            type=float,
            choices = [i / 100 for i in range(0, 100)],
            action=shared.DecimalAction,
            default=decimal.Decimal(0.3),
            help='f parameter [0-0.99] (default: 0.3).')
    optional.add_argument(
            '-o',
            '--out_prefix',
            dest='out_prefix',
            metavar='',
            required=False,
            type=str,
            action=shared.PathAction,
            default='./out.BAT',
            help='Prefix for output files (default: out.BAT).')
    optional.add_argument(
            '-p',
            '--proteins_fasta',
            dest='proteins_fasta',
            metavar='',
            required=False,
            type=str,
            action=shared.PathAction,
            help=('Path to predicted proteins fasta file. If supplied, BAT '
                'will skip the protein prediction step.'))
    optional.add_argument(
            '-a',
            '--diamond_alignment',
            dest='alignment_file',
            metavar='',
            required=False,
            type=str,
            action=shared.PathAction,
            help=('Path to alignment table. If supplied, BAT will skip the '
                'alignment step and directly classify the bin. A predicted '
                'proteins fasta file should also be supplied with argument '
                '[-p / --proteins].'))
    optional.add_argument(
            '--path_to_prodigal',
            dest='path_to_prodigal',
            metavar='',
            required=False,
            type=str,
            action=shared.PathAction,
            default='prodigal',
            help=('Path to Prodigal binaries. Supply if BAT can not '
                'find Prodigal.'))
    optional.add_argument(
            '--path_to_diamond',
            dest='path_to_diamond',
            metavar='',
            required=False,
            type=str,
            action=shared.PathAction,
            default='diamond',
            help=('Path to DIAMOND binaries. Supply if BAT can not find '
                'DIAMOND.'))
    optional.add_argument(
            '--no_stars',
            dest='no_stars',
            required=False,
            action='store_true',
            help='Suppress marking of suggestive classifications.')
    optional.add_argument(
            '--force',
            dest='force',
            required=False,
            action='store_true',
            help='Force overwrite existing files.')
    optional.add_argument(
            '-q',
            '--quiet',
            dest='quiet',
            required=False,
            action='store_true',
            help='Suppress verbosity.')
    optional.add_argument(
            '--verbose',
            dest='verbose',
            required=False,
            action='store_true',
            help='Increase verbosity.')
    optional.add_argument(
            '--no_log',
            dest='no_log',
            required=False,
            action='store_true',
            help='Suppress log file.')
    optional.add_argument(
            '-h',
            '--help',
            action='help',
            help='Show this help message and exit.')
    optional.add_argument(
            '--I_know_what_Im_doing',
            dest='IkwId',
            required=False,
            action='store_true',
            help='Flag for experimental features.')
    
    specific = parser.add_argument_group('DIAMOND specific optional arguments')
    
    specific.add_argument(
            '-n',
            '--nproc',
            dest='nproc',
            metavar='',
            required=False,
            type=int,
            default=multiprocessing.cpu_count(),
            help='Number of cores to deploy by DIAMOND (default: maximum).')
    specific.add_argument(
            '--sensitive',
            dest='sensitive',
            required=False,
            action='store_true',
            help='Run DIAMOND in sensitive mode (default: not enabled).')
    specific.add_argument(
            '--block_size',
            dest='block_size',
            metavar='',
            required=False,
            type=float,
            default=2.0,
            help=('DIAMOND block-size parameter (default: 2.0). Lower numbers '
                'will decrease memory and temporary disk space usage.'))
    specific.add_argument(
            '--index_chunks',
            dest='index_chunks',
            metavar='',
            required=False,
            type=int,
            default=4,
            help=('DIAMOND index-chunks parameter (default: 4). Set to 1 on '
                'high memory machines. The parameter has no effect on '
                'temporary disk space usage.'))
    specific.add_argument(
            '--tmpdir',
            dest='tmpdir',
            metavar='',
            required=False,
            type=str,
            action=shared.PathAction,
            help=('Directory for temporary DIAMOND files (default: directory '
                'to which output files are written).'))
    specific.add_argument(
            '--top',
            dest='top',
            metavar='',
            required=False,
            type=float,
            choices = [i for i in range(51)],
            default=50,
            help=('DIAMOND top parameter [0-50] (default: 50). Governs hits '
                'within range of best hit that are written to the alignment '
                'file. This is not the [-r / --range] parameter! Can only be '
                'set with the [--I_know_what_Im_doing] flag, see README.md.'))
    
    (args, extra_args) = parser.parse_known_args()

    extra_args = [arg for (i, arg) in enumerate(extra_args) if
                  (i, arg) != (0, 'bin')]
    if len(extra_args) > 0:
        sys.exit('error: too much arguments supplied:\n{0}'.format(
            '\n'.join(extra_args)))
        
    # Check experimental features.
    if not args.IkwId:
        if args.top < 50:
            sys.exit('error: --top can only be set lower than 50 in '
                     'combination with the --I_know_what_Im_doing flag. See '
                     'README.md as to why this is the case.')

    # Add extra arguments.
    shared.expand_arguments(args)
            
    return args


def run():
    args = parse_arguments()

    message = '# CAT v{0}.'.format(about.__version__)
    shared.give_user_feedback(message, args.log_file, args.quiet,
            show_time=False)
    
    # Check at which state to start.
    step_list = []
    if not args.proteins_fasta and not args.alignment_file:
        message = (
                '\n'
                'BAT is running. Protein prediction, alignment, and bin '
                'classification are carried out.')
        shared.give_user_feedback(message, args.log_file, args.quiet,
                show_time=False)

        step_list.append('predict_proteins')
        step_list.append('align')
    elif args.proteins_fasta and not args.alignment_file:
        message = (
                '\n'
                'BAT is running. Since a predicted protein fasta is supplied, '
                'only alignment and bin classification are carried out.')
        shared.give_user_feedback(message, args.log_file, args.quiet,
                show_time=False)

        step_list.append('align')
    elif args.proteins_fasta and args.alignment_file:
        message = (
                '\n'
                'BAT is running. Since a predicted protein fasta and '
                'alignment file are supplied, only bin classification is '
                'carried out.')
        shared.give_user_feedback(message, args.log_file, args.quiet,
                show_time=False)
    elif not args.proteins_fasta and args.alignment_file:
        message = (
                'if you want BAT to directly classify a single bin, you '
                'should not only supply an alignment table but also a '
                'predicted protein fasta file with argument '
                '[-p / --proteins].')
        shared.give_user_feedback(message, args.log_file, args.quiet,
                error=True)

        sys.exit(1)

    step_list.append('classify')

    # Print variables.
    message = (
            'Rarw!\n\n'
            'Supplied command: {0}\n\n'
            'Bin fasta: {1}\n'
            'Taxonomy folder: {2}\n'
            'Database folder: {3}\n'
            'Parameter r: {4}\n'
            'Parameter f: {5}\n'
            'Log file: {6}\n\n'
            '-----------------\n'.format(
                ' '.join(sys.argv),
                args.bin_fasta,
                args.taxonomy_folder,
                args.database_folder,
                float(args.r),
                float(args.f),
                args.log_file))
    shared.give_user_feedback(message, args.log_file, args.quiet,
            show_time=False)

    # Check binaries, output files, taxonomy folder and database folder, and
    # set variables.
    message = 'Doing some pre-flight checks first.'
    shared.give_user_feedback(message, args.log_file, args.quiet,
            show_time=False)

    errors = []
    
    errors.append(
            check.check_out_prefix(args.out_prefix, args.log_file, args.quiet))

    errors.append(
            check.check_bin_fasta(args.bin_fasta, args.log_file, args.quiet))
            
    if 'predict_proteins' in step_list:
        errors.append(
                check.check_prodigal_binaries(
                    args.path_to_prodigal, args.log_file, args.quiet))

        setattr(args,
                'proteins_fasta',
                '{0}.predicted_proteins.faa'.format(args.out_prefix))
        setattr(args,
                'proteins_gff',
                '{0}.predicted_proteins.gff'.format(args.out_prefix))

        if not args.force:
            errors.append(
                    check.check_output_file(
                        args.proteins_fasta, args.log_file, args.quiet))
            errors.append(
                    check.check_output_file(
                        args.proteins_gff, args.log_file, args.quiet))
            
    if 'align' in step_list:
        errors.append(
                check.check_diamond_binaries(
                    args.path_to_diamond, args.log_file, args.quiet))

        setattr(args,
                'alignment_file',
                '{0}.alignment.diamond'.format(args.out_prefix))

        if not args.force:
            errors.append(
                    check.check_output_file(
                        args.alignment_file, args.log_file, args.quiet))

    errors.append(
            check.check_folders_for_run(
                args.taxonomy_folder,
                args.nodes_dmp,
                args.names_dmp,
                args.database_folder,
                args.diamond_database,
                args.fastaid2LCAtaxid_file,
                args.taxids_with_multiple_offspring_file,
                step_list,
                args.log_file,
                args.quiet))

    setattr(args,
            'bin2classification_output_file',
            '{0}.bin2classification.txt'.format(args.out_prefix))
    setattr(args,
            'ORF2LCA_output_file',
            '{0}.ORF2LCA.txt'.format(args.out_prefix))

    if not args.force:
        errors.append(
                check.check_output_file(
                    args.bin2classification_output_file,
                    args.log_file,
                    args.quiet))
        errors.append(
                check.check_output_file(
                    args.ORF2LCA_output_file, args.log_file, args.quiet))
        
    if 'predict_proteins' not in step_list:
        errors.append(
                check.check_fasta(
                    args.proteins_fasta, args.log_file, args.quiet))

    # Print all variables.
    shared.print_variables(args, step_list)

    if True in errors:
        sys.exit(1)

    message = 'Ready to fly!\n\n-----------------\n'
    shared.give_user_feedback(message, args.log_file, args.quiet,
            show_time=False)
    
    # Start BAT.
    contig_names = shared.import_contig_names(
            args.bin_fasta, args.log_file, args.quiet)
    
    if 'predict_proteins' in step_list:
        shared.run_prodigal(
                args.path_to_prodigal,
                args.bin_fasta,
                args.proteins_fasta,
                args.proteins_gff,
                args.log_file,
                args.quiet)
        
    contig2ORFs = shared.import_ORFs(
            args.proteins_fasta, args.log_file, args.quiet)
    
    check.check_whether_ORFs_are_based_on_contigs(
            contig_names, contig2ORFs, args.log_file, args.quiet)
    
    if 'align' in step_list:
        shared.run_diamond(
                args.path_to_diamond,
                args.diamond_database,
                args.proteins_fasta,
                args.alignment_file,
                args.nproc,
                args.sensitive,
                args.block_size,
                args.index_chunks,
                args.tmpdir,
                args.top,
                args.log_file,
                args.quiet,
                args.verbose)

    (ORF2hits,
            all_hits) = shared.parse_tabular_alignment(
                    args.alignment_file,
                    args.one_minus_r,
                    args.log_file,
                    args.quiet)

    (taxid2parent,
            taxid2rank) = tax.import_nodes(
                    args.nodes_dmp, args.log_file, args.quiet)
    fastaid2LCAtaxid = tax.import_fastaid2LCAtaxid(
            args.fastaid2LCAtaxid_file, all_hits, args.log_file, args.quiet)
    taxids_with_multiple_offspring = tax.import_taxids_with_multiple_offspring(
            args.taxids_with_multiple_offspring_file,
            args.log_file,
            args.quiet)
    
    message = 'BAT is flying! Files {0} and {1} are created.'.format(
            args.bin2classification_output_file, args.ORF2LCA_output_file)
    shared.give_user_feedback(message, args.log_file, args.quiet)

    n_classified_bins = 0

    with open(args.bin2classification_output_file, 'w') as outf1, open(args.ORF2LCA_output_file, 'w') as outf2:
        outf1.write('# bin\tclassification\treason\tlineage\tlineage scores\n')
        outf2.write('# ORF\tbin\tlineage\tbit-score\n')

        # The list contains only a single bin, but I keep the code like this
        # to make the code consistent across bin and bins.
        bin_list = [args.bin_fasta.rsplit('/', 1)[-1]]
        for bin_ in bin_list:
            LCAs_ORFs = []
            
            for contig in sorted(contig_names):
                if contig not in contig2ORFs:
                    continue
                
                for ORF in contig2ORFs[contig]:
                    if ORF not in ORF2hits:
                        outf2.write('{0}\t{1}\tORF has no hit to database\n'
                                ''.format(ORF, bin_))
                        
                        continue
                    
                    (taxid,
                            top_bitscore) = tax.find_LCA_for_ORF(
                                    ORF2hits[ORF],
                                    fastaid2LCAtaxid,
                                    taxid2parent)
                     
                    if taxid.startswith('no taxid found'):
                        outf2.write('{0}\t{1}\t{2}\t{3}\n'.format(
                            ORF, bin_, taxid, top_bitscore))
                    else:
                        lineage = tax.find_lineage(taxid, taxid2parent)

                        if not args.no_stars:
                            lineage = tax.star_lineage(
                                    lineage, taxids_with_multiple_offspring)
                        
                        outf2.write('{0}\t{1}\t{2}\t{3}\n'.format(
                            ORF, bin_, ';'.join(lineage[::-1]), top_bitscore))
                                    
                    LCAs_ORFs.append((taxid, top_bitscore),)
                    
            if len(LCAs_ORFs) == 0:
                outf1.write('{0}\tunclassified\tno hits to database\n'.format(
                    bin_))

                continue
            
            (lineages,
                    lineages_scores,
                    based_on_n_ORFs) = tax.find_weighted_LCA(
                            LCAs_ORFs, taxid2parent, args.f)
             
            if lineages == 'no ORFs with taxids found.':
                outf1.write('{0}\tunclassified\t'
                        'hits not found in taxonomy files\n'.format(bin_))

                continue
            
            if lineages == 'no lineage whitelisted.':
                outf1.write(
                        '{0}\tunclassified\t'
                        'no lineage reached minimum bit-score support\n'
                        ''.format(bin_))

                continue
            
            # The bin has a valid classification.
            n_classified_bins += 1
            
            total_n_ORFs = sum([len(contig2ORFs[contig]) for
                contig in contig_names if contig in contig2ORFs])
            
            for (i, lineage) in enumerate(lineages):
                if not args.no_stars:
                    lineage = tax.star_lineage(
                            lineage, taxids_with_multiple_offspring)
                
                scores = ['{0:.2f}'.format(score) for
                        score in lineages_scores[i]]
                
                if len(lineages) == 1:
                    # There is only one classification.
                    outf1.write(
                            '{0}\t'
                            'classified\t'
                            'based on {1}/{2} ORFs\t'
                            '{3}\t'
                            '{4}\n'.format(
                                bin_,
                                based_on_n_ORFs,
                                total_n_ORFs,
                                ';'.join(lineage[::-1]),
                                ';'.join(scores[::-1])))
                else:
                    # There are multiple classifications.
                    outf1.write(
                            '{0}\t'
                            'classified ({1}/{2})\t'
                            'based on {3}/{4} ORFs\t'
                            '{5}\t'
                            '{6}\n'.format(
                                bin_,
                                i + 1,
                                len(lineages),
                                based_on_n_ORFs,
                                total_n_ORFs,
                                ';'.join(lineage[::-1]),
                                ';'.join(scores[::-1])))
                                   
    message = ('\n-----------------\n'
               '[{0}] BAT is done! {1}/1 bin classified.'.format(
                   datetime.datetime.now(),
                   n_classified_bins))
    shared.give_user_feedback(message, args.log_file, args.quiet,
            show_time=False)
  
    if args.f < 0.5:
        message = ('WARNING: since f is set to smaller than 0.5, one bin '
                   'may have multiple classifications.')
        shared.give_user_feedback(message, args.log_file, args.quiet,
                show_time=False)

    return


if __name__ == '__main__':
    sys.exit('Run \'CAT bins\' to run Bin Annotation Tool (BAT) on a single '
            'bin.')

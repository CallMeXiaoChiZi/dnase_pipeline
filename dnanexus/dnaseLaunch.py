#!/usr/bin/env python
# dnaseLaunch.py 0.0.1

import argparse,os, sys, json

import dxpy
#from dxencode import dxencode as dxencode
import dxencode as dxencode
from launch import Launch

class DnaseLaunch(Launch):
    '''Descendent from Launch class with 'rampage' methods'''

    PIPELINE_NAME = "dnase-seq"
    ''' This must match the assay type returned by dxencode.get_assay_type({exp_id}).'''
    PIPELINE_HELP = "Launches '"+PIPELINE_NAME+"' pipeline " + \
                    "analysis for one replicate or combined replicates. "
    ''' This help title should name pipline and whether combined replicates are supported.'''
                    
    RESULT_FOLDER_DEFAULT = '/dnase/'
    ''' This the default location to place results folders for each experiment.'''
    
    PIPELINE_BRANCH_ORDER = [ "TECH_REP", "BIO_REP", "COMBINED_REPS" ]
    '''A pipeline is frequently made of branches that flow into each other, such as replicate level to combined replicate.'''
    
    PIPELINE_BRANCHES = {
    #'''Each branch must define the 'steps' and their (artificially) linear order.'''
        "TECH_REP": {
                "ORDER": { "se": [ "dnase-align-bwa-se" ],
                           "pe": [ "dnase-align-bwa-pe" ] },
                "STEPS": {
                            "dnase-align-bwa-se": {
                                "inputs": { "reads": "reads", "bwa_index": "bwa_index" },
                                "app": "dnase-align-bwa-se", 
                                "params": {"nthreads": "nthreads"}, 
                                "results": {
                                    "bam_techrep":      "bam_bwa", 
                                    "bam_techrep_qc":   "bam_bwa_qc",
                                },
                                #"output_values": { "reads_bwa": "reads" },
                            },
                            "dnase-align-bwa-pe": {
                                "inputs": { "reads1": "reads1", "reads2": "reads2", "bwa_index": "bwa_index" }, 
                                "app": "dnase-align-bwa-pe", 
                                "params": { "nthreads": "nthreads" }, 
                                "results": {
                                    "bam_techrep":      "bam_bwa", 
                                    "bam_techrep_qc":   "bam_bwa_qc",
                                },
                                #"output_values": { "reads_techrep": "reads" },
                            }, 
                }
        },
        "BIO_REP":  {
                "ORDER": { "se": [  "dnase-merge-bams", 
                                    "dnase-filter-se", 
                                    "dnase-size-bam",      
                                    "dnase-eval-bam-se", 
                                    "biorep-call-hotspots", 
                                    "dnase-hotspot-qc" ],
                           "pe": [  "dnase-merge-bams", 
                                    "dnase-filter-pe", 
                                    "dnase-size-bam",
                                    "dnase-eval-bam-pe", 
                                    "biorep-call-hotspots", 
                                    "dnase-hotspot-qc" ] },
                "STEPS": {
                            "dnase-merge-bams": {
                                "inputs": { "bam_ABC":    "bam_set" },
                                "app": "dnase-merge-bams", 
                                "params": { "nthreads": "nthreads" }, 
                                "results": {
                                    "bam_biorep":      "bam_biorep", 
                                    "bam_biorep_qc":   "bam_biorep_qc",
                                },
                                #"output_values": { "reads_biorep": "reads" },
                            },
                            "dnase-filter-pe": {
                                "inputs": { "bam_biorep": "bam_bwa" }, 
                                "app": "dnase-filter-pe", 
                                "params": { "map_thresh": "map_thresh", "nthreads": "nthreads" }, 
                                "results": {
                                    "bam_filtered":         "bam_filtered", 
                                    "bam_filtered_qc":      "bam_filtered_qc", 
                                },
                                "output_values": { "reads_filtered": "reads" },
                            },
                            "dnase-filter-se": {
                                "inputs": { "bam_biorep": "bam_bwa" }, 
                                "app": "dnase-filter-se", 
                                "params": { "map_thresh": "map_thresh", "nthreads": "nthreads" }, 
                                "results": {
                                    "bam_filtered":         "bam_filtered", 
                                    "bam_filtered_qc":      "bam_filtered_qc", 
                                },
                                "output_values": { "reads_filtered": "reads" },
                            }, 
                            "dnase-size-bam": {
                                "inputs": { "bam_filtered": "unsized_bam" }, 
                                "app": "dnase-size-bam", 
                                "params": { "target_size": "target_size", "upper_limit": "upper_limit" },
                                "param_links": { "target_size": {"name":"reads_filtered", "rep":"sister"} }, 
                                "results": {
                                    "bam_sized":            "bam_sized", 
                                    "bam_sized_qc":         "bam_sized_qc", 
                                },
                                #"output_values": { "reads_sized": "reads" },
                            }, 
                            "dnase-eval-bam-pe": {
                                "inputs": { "bam_sized": "bam_sized" }, 
                                "app": "dnase-eval-bam-pe", 
                                "params": { "sample_size": "sample_size" }, 
                                "results": {
                                    "bam_no_chrM":          "bam_no_chrM", 
                                    "bam_no_chrM_qc":       "bam_no_chrM_qc", 
                                    "bam_sample":           "bam_sample", 
                                    "bam_sample_qc":        "bam_sample_qc", 
                                },
                                #"output_values": { "reads_no_chrM": "reads" },
                            },
                            "dnase-eval-bam-se": {
                                "inputs": { "bam_sized":    "bam_sized" }, 
                                "app": "dnase-eval-bam-se", 
                                "params": { "sample_size": "sample_size" }, 
                                "results": {
                                    "bam_no_chrM":          "bam_no_chrM", 
                                    "bam_no_chrM_qc":       "bam_no_chrM_qc", 
                                    "bam_sample":           "bam_sample", 
                                    "bam_sample_qc":        "bam_sample_qc", 
                                },
                                #"output_values": { "reads_no_chrM": "reads" },
                            }, 
                            "biorep-call-hotspots": {
                                "inputs": { "bam_no_chrM": "bam_to_call", "chrom_sizes": "chrom_sizes" }, 
                                "app": "dnase-call-hotspots", 
                                "params": { "read_length": "read_length", "genome": "genome" }, 
                                "results": {
                                     "br_bb_hotspot_broadPeak":   "bb_hotspot_broadPeak", 
                                    "br_bed_hotspot_broadPeak":  "bed_hotspot_broadPeak", 
                                     "br_bb_hotspot_narrowPeak":  "bb_hotspot_narrowPeak",
                                    "br_bed_hotspot_narrowPeak": "bed_hotspot_narrowPeak", 
                                     "br_bw_hotspot_signal":      "bw_hotspot_signal", 
                                    "br_bam_hotspot_qc":         "bam_hotspot_qc"
                                },
                            }, 
                            "dnase-hotspot-qc": {
                                "inputs": { "bam_no_chrM": "bam_to_sample", "chrom_sizes": "chrom_sizes" }, 
                                "app": "dnase-hotspot-qc", 
                                "params": { "read_length": "read_length", "genome": "genome"}, 
                                "results": {
                                    "bam_sample_5M":        "bam_sample_5M",
                                    "bam_sample_5M_qc":     "bam_sample_5M_qc", 
                                },
                                #"output_values": { "reads_sample_5M": "reads" },
                            }
                }
        },
        "COMBINED_REPS": {
                "ORDER": [ "dnase-pool-bioreps", "pooled-call-hotspots" ],
                "STEPS": {
                            "dnase-pool-bioreps": {
                                "inputs": {
                                       "bam_A":    "bam_A",    "bam_B":    "bam_B", 
                                    "signal_A": "signal_A", "signal_B": "signal_B", 
                                     "peaks_A":  "peaks_A",  "peaks_B":  "peaks_B", 
                                    "chrom_sizes": "chrom_sizes" 
                                }, 
                                "app": "dnase-pool-bioreps", 
                                "params": {}, 
                                "results": {
                                    "bam_pooled":       "bam_pooled", 
                                    "bed_merged":       "bed_merged", 
                                    "bb_merged":        "bb_merged", 
                                    "pooled_qc":        "pooled_qc", 
                                },
                                #"output_values": { "reads_pooled": "reads" },
                            },
                            "pooled-call-hotspots": {
                                "inputs": { "bam_pooled": "bam_to_call", "chrom_sizes": "chrom_sizes" }, 
                                "app": "dnase-call-hotspots", 
                                "params": { "read_length": "read_length", "genome": "genome" }, 
                                "results": {
                                     "pr_bb_hotspot_broadPeak":   "bb_hotspot_broadPeak", 
                                    "pr_bed_hotspot_broadPeak":  "bed_hotspot_broadPeak", 
                                     "pr_bb_hotspot_narrowPeak":  "bb_hotspot_narrowPeak",
                                    "pr_bed_hotspot_narrowPeak": "bed_hotspot_narrowPeak", 
                                     "pr_bw_hotspot_signal":      "bw_hotspot_signal", 
                                    "pr_bam_hotspot_qc":         "bam_hotspot_qc" 
                                }
                            } 
                }
        }
    }

    FILE_GLOBS = {
        #"reads":                    "/*.fq.gz",
        #"reads1":                   "/*.fq.gz",
        #"reads2":                   "/*.fq.gz",
        # dnase-align-pe/se results:
        "bam_techrep":              "/*_bwa_techrep.bam", 
        "bam_techrep_qc":           "/*_bwa_techrep_qc.txt",
        # dnase-merge-bams input/results:
        "bam_ABC":                  "/*_bwa_techrep.bam", 
        "bam_biorep":               "/*_biorep.bam", 
        "bam_biorep_qc":            "/*_biorep_qc.txt", 
        # dnase-filter-pe/se results:
        "bam_filtered":             "/*_filtered.bam", 
        "bam_filtered_qc":          "/*_filtered_qc.txt", 
        # dnase-size-bam results:
        "bam_sized":                "/*_sized.bam", 
        "bam_sized_qc":             "/*_sized_qc.txt", 
        # dnase-eval-bam-pe/se results:
        "bam_no_chrM":              "/*_no_chrM.bam", 
        "bam_no_chrM_qc":           "/*_no_chrM_qc.txt", 
        "bam_sample":               "/*_sample.bam", 
        "bam_sample_qc":            "/*_sample_qc.txt",
        # biorep-call-hotspots input/results:
        #"bam_to_call":              "/*_no_chrM.bam", 
        "br_bb_hotspot_broadPeak":  "/*_no_chrM_broadPeak_hotspot.bb", 
        "br_bed_hotspot_broadPeak": "/*_no_chrM_broadPeak_hotspot.bed", 
        "br_bed_hotspot_narrowPeak":"/*_no_chrM_narrowPeak_hotspot.bed", 
        "br_bb_hotspot_narrowPeak": "/*_no_chrM_narrowPeak_hotspot.bb",
        "br_bw_hotspot_signal":     "/*_no_chrM_signal_hotspot.bw", 
        "br_bam_hotspot_qc":        "/*_no_chrM_hotspot_qc.txt", 
        # dnase-hotspot-qc results:
        "bam_sample_5M":            "/*_sample_5M.bam", 
        "bam_sample_5M_qc":         "/*_sample_5M_qc.txt", 
        # dnase-pool-bioreps input/results:
        "bam_A":                    "/*_filtered.bam",
        "bam_B":                    "/*_filtered.bam",
        "signal_A":                 "/*_no_chrM_signal_hotspot.bw",
        "signal_B":                 "/*_no_chrM_signal_hotspot.bw",
        "peaks_A":                  "/*_no_chrM_narrowPeak_hotspot.bb",
        "peaks_B":                  "/*_no_chrM_narrowPeak_hotspot.bb",
        "bam_pooled":               "/*_pooled.bam", 
        "bed_merged":               "/*_merged_narrowPeak.bed", 
        "bb_merged":                "/*_merged_narrowPeak.bb", 
        "pooled_qc":                "/*_pooled_qc.txt", 
        # biorep-call-hotspots input/results:
        #"bam_to_call":              "/*_pooled.bam", 
        "pr_bb_hotspot_broadPeak":  "/*_pooled_broadPeak_hotspot.bb", 
        "pr_bed_hotspot_broadPeak": "/*_pooled_broadPeak_hotspot.bed", 
        "pr_bed_hotspot_narrowPeak":"/*_pooled_narrowPeak_hotspot.bed", 
        "pr_bb_hotspot_narrowPeak": "/*_pooled_narrowPeak_hotspot.bb",
        "pr_bw_hotspot_signal":     "/*_pooled_signal_hotspot.bw", 
        "pr_bam_hotspot_qc":        "/*_pooled_hotspot_qc.txt",         
    }

    REF_PROJECT_DEFAULT = "scratchPad"  # TODO: move all ref files to ref project!
    REFERENCE_FILES = {
        # For looking up reference file names.
        # TODO: should use ACCESSION based fileNames
        "bwa_index":   {
                        "hg19": {
                                "female":   "hg19_female_bwa_index.tgz",
                                "male":     "hg19_male_bwa_index.tgz"
                                }
                        },
        "chrom_sizes":   {
                        "hg19": {
                                "female":   "female.hg19.chrom.sizes",
                                "male":     "male.hg19.chrom.sizes"
                                },
                        "mm10": {
                                "female":   "female.mm10.chrom.sizes",
                                "male":     "male.mm10.chrom.sizes"
                                }
                        }
        }


    def __init__(self):
        Launch.__init__(self)
        
    def get_args(self):
        '''Parse the input arguments.'''
        ap = Launch.get_args(self,parse=False)
        
        ap.add_argument('-rl', '--read_length',
                        help='The length of reads.',
                        type=int,
                        choices=['32', '36', '40', '50', '58', '72', '76', '100'],
                        default='100',
                        required=False)

        # NOTE: Could override get_args() to have this non-generic control message
        #ap.add_argument('-c', '--control',
        #                help='The control bam for peak calling.',
        #                required=False)

        return ap.parse_args()

    def pipeline_specific_vars(self,args,verbose=False):
        '''Adds pipeline specific variables to a dict, for use building the workflow.'''
        psv = Launch.pipeline_specific_vars(self,args)
        
        #if not psv['paired_end']:
        #    print "Rampage is always expected to be paired-end but mapping says otherwise."
        #    sys.exit(1)

        # Some specific settings
        psv['nthreads']    = 8
        psv['map_thresh']  = 3
        psv['sample_size'] = 15000000
        psv['read_length'] = args.read_length
        psv['upper_limit'] = 0
        
        if verbose:
            print "Pipeline Specific Vars:"
            print json.dumps(psv,indent=4)
        return psv


    def find_ref_files(self,priors):
        '''Locates all reference files based upon organism and gender.'''
        # TODO:  move all ref files to ref project and replace "/ref/" and self.REF_PROJECT_DEFAULT
        #bwaIx = self.psv['refLoc']+self.REFERENCE_FILES['bwa_index'][self.psv['genome']][self.psv['gender']]
        bwaIx = "/ref/"+self.REFERENCE_FILES['bwa_index'][self.psv['genome']][self.psv['gender']]
        #bwaIxFid = dxencode.find_file(bwaIx,dxencode.REF_PROJECT_DEFAULT)
        bwaIxFid = dxencode.find_file(bwaIx,self.REF_PROJECT_DEFAULT)
        if bwaIxFid == None:
            sys.exit("ERROR: Unable to locate BWA index file '" + bwaIx + "'")
        else:
            priors['bwa_index'] = bwaIxFid

        chromSizes = self.psv['refLoc']+self.REFERENCE_FILES['chrom_sizes'][self.psv['genome']][self.psv['gender']]
        chromSizesFid = dxencode.find_file(chromSizes,dxencode.REF_PROJECT_DEFAULT)
        if chromSizesFid == None:
            sys.exit("ERROR: Unable to locate Chrom Sizes file '" + chromSizes + "'")
        else:
            priors['chrom_sizes'] = chromSizesFid
        self.psv['ref_files'] = self.REFERENCE_FILES.keys()
    

    def add_combining_reps(self, psv):
        '''Defines how replicated are combined.'''
        # OVERRIDING parent because DNase-seq pipeline doesn't follow the standard replicate combination model
        debug=False
        
        reps = psv['reps']
        # In the 'standard combining model' PIPELINE_BRANCH_ORDER = [ "REP", "COMBINED_REPS" ]
        # and all replicates are in psv['reps'] keyed as 'a','b',... and having rep['rep_tech'] = 'rep1_1'
        # All these simple reps will have rep['branch_id'] = "REP"
        
        # First, each tech_rep is processed individually
        bio_reps = []
        for rep_id in sorted( reps.keys() ):
            if len(rep_id) == 1: # single letter: simple replicate
                rep = reps[rep_id]
                rep['branch_id'] = "TECH_REP"
                if rep['br'] not in bio_reps:
                    bio_reps.append(rep['br'])
                else:
                    self.combined_reps = True  # More than one tech_rep per bio_rep so combining will be done!
                if debug:
                    print "DEBUG: rep: " + rep_id
                    
        # Next bio_reps have their technical replicates merged and processing continues
        for bio_rep in bio_reps:
            river = {}
            river['branch_id'] = "BIO_REP"
            river['tributaries'] = []
            river['rep_tech'] = 'reps' + str(bio_rep) + '_'  # reps1_1.2.3 is rep1_1 + rep1_2 + rep1_3
            river['br'] = bio_rep
            for tributary_id in sorted( reps.keys() ): 
                if len(tributary_id) == 1:
                    tributary = reps[tributary_id]
                    if tributary['br'] == bio_rep:
                        if len(river['tributaries']) > 0:
                            river['rep_tech'] += '.'
                        river['rep_tech'] += tributary['rep_tech'][5:]
                        river['tributaries'].append(tributary_id)
            assert len(river['tributaries']) >= 1  # It could be the case that there is one tech_rep for a bio_rep!
            # river_id for ['a','b'] = 'b-bio_rep1'
            river_id = river['tributaries'][-1] + '-bio_rep' + str(bio_rep)
            reps[river_id] = river
            # Special case of 2 allows for designating sisters
            if len(river['tributaries']) == 2:
                reps[river['tributaries'][0]]['sister'] = river['tributaries'][1]
                reps[river['tributaries'][1]]['sister'] = river['tributaries'][0]
            if debug:
                print "DEBUG: biorep: " + river_id + " tributaries: " + str(len(river['tributaries']))

        # Finally a pair of bio_reps are merged and processing finishes up
        if len(bio_reps) == 2:
            self.combined_reps = True  # More than one bio_rep so combining will be done!
            sea = {} # SEA is the final branch into which all tributaries flow
            sea['branch_id'] = 'COMBINED_REPS'
            sea['tributaries'] = []
            sea['rep_tech'] = 'reps'
            for tributary_id in sorted( reps.keys() ):
                if len(tributary_id) == 1:  # ignore the simple reps
                    continue 
                tributary = reps[tributary_id]
                if len(sea['tributaries']) > 0:
                    sea['rep_tech'] += '-'
                sea['rep_tech'] += tributary['rep_tech'][4:]
                sea['tributaries'].append(tributary_id)
        
            psv['rep_tech'] = sea['rep_tech']
            reps[self.SEA_ID] = sea
            # Special case of 2 allows for designating sisters
            reps[sea['tributaries'][0]]['sister'] = sea['tributaries'][1]
            reps[sea['tributaries'][1]]['sister'] = sea['tributaries'][0]
        #else:
        #    print "Found " + str(len(bio_reps)) + " bio_reps.  If exactly two, they would be combined."
        #print json.dumps(reps,indent=4,sort_keys=True)
            

    #######################


if __name__ == '__main__':
    '''Run from the command line.'''
    dnaseLaunch = DnaseLaunch()
    dnaseLaunch.run()

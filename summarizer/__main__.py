'''
Main entry point for our text summarization program.

Copyright, 2015.

Authors:
Luis Perez (luis.perez.live@gmail.com)
Kevin Eskici (keskici@college.harvar.edu)

For help in running this package, run:
    python -m summarizer --help
from the parent directory.
'''
import os
import traceback
import pyrouge

from optparse import OptionParser
from . import grasshopper
from . import baselines
from . import textrank

# Dictionary mapping algorithm commandline parameters to
# their respective algorithm classes.
argsToAlgo = {
    'grasshopper':   grasshopper.run_grassHopper,
    'geomprior':   baselines.geomPriorBaseline,
    'firstgeomprior':   baselines.modifiedGeomPriorBaseline,
    'frequency':   baselines.wordFreqBaseline,
    'textrank': textrank.textRank}


def createSummaries(sum_algo, abs_path, out_path, k=5, multiDocument=False):
    # Extracted from the input folder name
    setID = abs_path.split('/')[-1]

    # Stores DocumentIDs
    docIDs = []

    # Create document set that we wish to evaluate
    D = []
    for filename in os.listdir(abs_path):
        # Only take files that we've parsed before!
        tmp = filename.split('.')
        if tmp[0] == 'parsed':
            docIDs.append(tmp[1])
            filepath = os.path.join(abs_path, filename)
            with open(filepath) as inputDoc:
                D.append(inputDoc.readlines())

    # Pass this to the algorithm which should return the summary as
    # a list of sentences.
    if multiDocument:
        summary = sum_algo(D, k)
        # Write out the summary
        filepath = os.path.join(out_path, "SetSummary.{}.txt".format(setID))
        with open(filepath, 'w+') as out:
            for s in summary:
                out.write("{}.\n".format(s.strip()))
    else:
        for i in range(len(D)):
            summary = sum_algo([D[i]], k)
            filepath = os.path.join(
                out_path, "Summary.{}.txt".format(docIDs[i]))
            with open(filepath, 'w+') as out:
                for s in summary:
                    out.write("{}.\n".format(s.strip()))


def parseArgs(parser):
    parser.add_option("-d", "--data_dir", default=None,
                      help="Base Directory containing summarization documents" +
                      " and model summaries. Summarization documents should be" +
                      " contained in the docs/ subdirectory. See README for" +
                      " details. If no directory is provided, input is streamed" +
                      " from STDIN and results are output to STDOUT. ROUGE" +
                      " analysis is not performed.")
    parser.add_option("-a", "--algorithm", default="frequency",
                      help="Algorithm to use for summarization. Output" +
                      " summaries are saved under the DATA_DIR/ALGORITHM/" +
                      " directory if a data_dir parameter is provided." +
                      "Current options are {}".format(argsToAlgo.keys()) +
                      "If None is input, the summarization is not run. This is" +
                      " useful if summaries have been created and you want to" +
                      " just score them with ROUGE.")
    parser.add_option("-s", "--rouge_score", default=False,
                      help="The paremeter is ignored in the case where DATA_DIR " +
                      "is not set. Otherwise, if ROUGE_SCORE, then the model " +
                      "and system summaries are scored using the ROUGE metrics " +
                      "and results are printed to STDOUT.")
    parser.add_option("--debug", default=False,
                      help="Prints helpful debugging information.")


def run(opts):
    '''
    Runs our summarization software based on user options.
    '''
    # TODO(nautilik): stream input from stdin if opts.data_dir is None
    base = os.path.abspath(opts.data_dir)
    if base is None:
        raise Exception(
            "You must provided a DATA_DIR. STDIN currently not supported.")
    outpath = os.path.join(base, opts.algorithm)
    try:
        algorithm = argsToAlgo[opts.algorithm.lower()]
    except KeyError:
        raise Exception(
            "{} is not an available algorithm!".format(opts.algorithm))

    # Create directory if it does not exist
    if not os.path.exists(outpath):
        os.makedirs(outpath)

    inbase = os.path.join(base, 'docs')
    folders = dirs = [d for d in os.listdir(
        inbase) if os.path.isdir(os.path.join(inbase, d))]
    for folder in folders:
        inpath = os.path.join(inbase, folder)
        try:
            createSummaries(algorithm, inpath, outpath, multiDocument=True)
        except Exception as e:
            print "Failed with {}".format(inpath)
            if opts.debug:
                print traceback.print_exc()

    # If rouge score is input, attempt to score the results with pyrouge
    # Currently only handles multiple documents!
    if opts.data_dir is not None and opts.rouge_score:
        r = pyrouge.Rouge155()
        r.system_dir = os.path.join(opts.data_dir, 'system_multi')
        r.model_dir = outpath
        r.system_filename_pattern = 'SetSummary.(\d+).txt'
        r.model_filename_pattern = 'SetSummary.#ID#.[A-Z].txt'

        output = r.convert_and_evaluate()

        print output


def main():
    '''
    Main program
    '''

    parser = OptionParser()
    parseArgs(parser)
    options, args = parser.parse_args()
    run(options)


if __name__ == '__main__':
    main()

# How to Use biocommons.seqrepo

We use biocommons.seqrepo to load human and mouse genome sequences locally, which is used for generating SPDI for variants.

## Pulling human genome sequences

To load human genome sequences, you can follow the instruction [here](https://github.com/biocommons/biocommons.seqrepo). The file to load is GCF_000001635.27_GRCm39_genomic.fna.

## Loading mouse genome sequences

1. Download Genome sequences (FASTA) files [here](https://www.ncbi.nlm.nih.gov/datasets/genome/GCF_000001635.27/).

2. Initiate the folder.

    ```bash
    seqrepo init
    ```

3. Load the file.

    ```bash
    seqrepo load -n RefSeq  GCF_000001635.27_GRCm39_genomic.fna
    ```

4. Check the folder. The data should be loaded in /usr/local/share/seqrepo/master. You can rename the folder to /usr/local/share/seqrepo/mouse.

5. Follow the same instruction in pulling human genome sequences to connect to the database.

6. Check if you can get the mouse sequence:

    ```python
    # Simple Pythonic interface to sequences
    from biocommons.seqrepo import SeqRepo
    sr = SeqRepo("/usr/local/share/seqrepo/mouse")
    sr["NC_000067.7"][780000:780020]
    ```

import csv
from adapters import Adapter

# Example TF motif file from HOCOMOCO (e.g. ATF1_HUMAN.H11MO.0.B.pwm), which adastra used.
# Each pwm (position weight matrix) is a N x 4 matrix, where N is the length of the TF motif.
# >ATF1_HUMAN.H11MO.0.B
# 0.13987841615191168	0.3608848685361665	-0.4517428977281205	-0.25006525443490907
# 0.3553616298110878	-0.7707228823699511	0.3663777685862727	-0.4032800768485152
# 0.338606483241983	-0.8414816866844361	0.7066714674964639	-1.975404324094267
# -2.4841943814369576	-3.324736791140142	-1.9754043240942667	1.3195988707291637
# -2.3936647653320064	-2.9606438896517475	1.328010168941795	-2.4841943814369576
# 1.3217083373824634	-2.9606438896517475	-2.5837428525823363	-2.0963708769895044
# -1.9754043240942667	1.191348924768384	-1.4888815002078464	-1.0666727869454955
# -2.2340103118057417	-2.5837428525823363	1.2450934398879747	-1.0666727869454955
# -1.1380405061628662	0.23796182230991783	-2.5837428525823363	0.8481840389725303
# 0.13987841615191168	0.6170180100710398	-0.5426512454816383	-0.8788317538331962
# 0.7561011054759478	-0.7707228823699511	-0.2914989252431338	-0.4151773801942997


class Motif(Adapter):
    # other var should be in const?

    def __init__(self, filepath, tf_ids, source, type='node'):
        self.filepath = filepath
        self.tf_name = filepath.split('.')[0]
        self.tf_ids = tf_ids
        self.source = source
        self.type = type  # seperate all create node & edge at once?
        if type == 'node':
            self.dataset = 'motif'  # dataset vs label?
            self.label = 'motif'
        elif type == 'edge':
            self.dataset = 'motif to protein'
            self.label = 'motif to protein'

        super().__init__()

    def get_TF_uniprot_id(self):
        with open(self.tf_ids, 'r') as tf_uniprot_mapfile:
            tf_uniprot_csv = csv.reader(tf_uniprot_mapfile, delimiter='\t')
            next(tf_uniprot_csv)
            for row in tf_uniprot_csv:
                if row[0] == self.tf_name:
                    return row[1]  # return uniprot id of the TF (i.e. protein)
        return None

    def process_file(self):
        if self.type == 'node':
            pwm = []
            with open(self.filepath, 'r') as pwm_file:
                next(pwm_file)
                for line in pwm_file:
                    pwm_row = line.strip().split()
                    pwm.append([float(value)
                               for value in pwm_row])  # round? flatten?
            length = len(pwm)

            _id = self.tf_name + self.source  # ??check
            _props = {
                'tf_name': self.tf_name,
                'source': self.source,
                # 'source_url':
                'pwm': pwm,
                'length': length
            }
            yield(_id, self.label, _props)  # or just return?

        elif self.type == 'edge':
            tf_uniprot_id = self.get_TF_uniprot_id()
            if tf_uniprot_id is None:
                print(
                    'TF uniprot id unavailable, skipping motif to protein edge: ' + self.filepath)
                return

            _id = self.tf_name + self.source + tf_uniprot_id  # check
            _source = 'motifs/' + self.tf_name + self.source  # ??check
            _target = 'proteins/' + tf_uniprot_id
            _props = {
                'source': self.source
            }
            yield(_id, _source, _target, self.label, _props)
        # nodes & edges in two steps or at once?

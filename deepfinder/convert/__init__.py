import xml.etree.ElementTree as ET
from xml.dom import minidom

def objl_read(filename):
    tree = ET.parse(filename)
    objl_xml = tree.getroot()

    objl = []
    for p in range(len(objl_xml)):
        # Mandatory attributes:
        lbl = int(objl_xml[p].get('class_label'))
        x = float(objl_xml[p].get('x'))
        y = float(objl_xml[p].get('y'))
        z = float(objl_xml[p].get('z'))

        # Optional attributes:
        tidx = objl_xml[p].get('tomo_idx')
        objid = objl_xml[p].get('obj_id')
        psi = objl_xml[p].get('psi')
        phi = objl_xml[p].get('phi')
        the = objl_xml[p].get('the')
        csize = objl_xml[p].get('cluster_size')

        # if optional attributes exist, then cast to correct type:
        if tidx != None:
            tidx = int(tidx)
        if objid != None:
            objid = int(objid)
        if csize != None:
            csize = int(csize)
        if psi != None or phi != None or the != None:
            psi = float(psi)
            phi = float(phi)
            the = float(the)

        obj = {
            'tomo_idx': tidx,
            'obj_id': objid,
            'label': lbl,
            'x': x,
            'y': y,
            'z': z,
            'psi': phi,
            'phi': psi,
            'the': the,
            'cluster_size': csize
        }

        objl.append(obj)
    return objl


def objl_write(objl, filename):
    objl_xml = ET.Element('objlist')
    for idx in range(len(objl)):
        tidx  = objl[idx]['tomo_idx']
        objid = objl[idx]['obj_id']
        lbl   = objl[idx]['label']
        x     = objl[idx]['x']
        y     = objl[idx]['y']
        z     = objl[idx]['z']
        psi   = objl[idx]['psi']
        phi   = objl[idx]['phi']
        the   = objl[idx]['the']
        csize = objl[idx]['cluster_size']

        obj = ET.SubElement(objl_xml, 'object')
        if tidx!=None:
            obj.set('tomo_idx', str(tidx))
        if objid!=None:
            obj.set('obj_id', str(objid))
        obj.set('class_label' , str(lbl))
        obj.set('x'           , '%.3f' % x)
        obj.set('y'           , '%.3f' % y)
        obj.set('z'           , '%.3f' % z)
        if psi!=None:
            obj.set('psi', '%.3f' % psi)
        if phi!=None:
            obj.set('phi', '%.3f' % phi)
        if the!=None:
            obj.set('the', '%.3f' % the)
        if csize!=None:
            obj.set('cluster_size', str(csize))

    tree = ET.ElementTree(objl_xml)
    tree.write(filename)



def objl_add(objl, label, coord, obj_id=None, tomo_idx=None, orient=(None, None, None), cluster_size=None):
    obj = {
        'tomo_idx': tomo_idx,
        'obj_id': obj_id,
        'label': label,
        'x': coord[2],
        'y': coord[1],
        'z': coord[0],
        'psi': orient[0],
        'phi': orient[1],
        'the': orient[2],
        'cluster_size': cluster_size
    }
    objl.append(obj)
    return objl


def objl_get_labels(objl):
    """
    Returns a list with different (unique) labels contained in input objl
    """
    class_list = []
    for idx in range(len(objl)):
        class_list.append(objl[idx]['label'])
    # Set only stores a value once even if it is inserted more then once:
    lbl_set  = set(class_list) # insert the list to the set
    lbl_list = (list(lbl_set)) # convert the set to the list
    return lbl_list


def objl_get_class(objl, label):
    """
    Get all objects of specified class.

    Args:
        objl (list of dict)
        label (int)
    Returns:
        list of dict: contains only objects from class 'label'
    """
    idx_class = []
    for idx in range(len(objl)):
        if str(objl[idx]['label'])==str(label):
            idx_class.append(idx)

    objlOUT = []
    for idx in range(len(idx_class)):
        objlOUT.append(objl[idx_class[idx]])
    return objlOUT

def objl_get_tomo(objl, tomo_idx):
    """
    Get all objects originating from tomo 'tomo_idx'.

    Args:
        objl (list of dict): contains objects from various tomograms
        tomo_idx (int): tomogram index
    Returns:
        list of dict: contains objects from tomogram 'tomo_idx'
    """
    idx_tomo = []
    for idx in range(len(objl)):
        if objl[idx]['tomo_idx'] == tomo_idx:
            idx_tomo.append(idx)

    objlOUT = []
    for idx in range(len(idx_tomo)):
        objlOUT.append(objl[idx_tomo[idx]])
    return objlOUT

def objl_disp(objlIN):
    """Prints objl in terminal"""
    for p in range(len(objlIN)):
        tidx  = objlIN[p]['tomo_idx']
        objid = objlIN[p]['obj_id']
        lbl   = objlIN[p]['label']
        x     = objlIN[p]['x']
        y     = objlIN[p]['y']
        z     = objlIN[p]['z']
        psi   = objlIN[p]['psi']
        phi   = objlIN[p]['phi']
        the   = objlIN[p]['the']
        csize = objlIN[p]['cluster_size']

        strout = 'obj ' + str(p) + ': ('
        if tidx!=None:
            strout = strout + 'tomo_idx:' + str(tidx) + ', '
        if objid!=None:
            strout = strout + 'obj_id:' + str(objid) + ', '
        strout = strout + 'lbl:' + str(lbl) + ', x:' + str(x) + ', y:' + str(y) + ', z:' + str(z) + ', '
        if psi!=None or phi!=None or the!=None:
            strout = strout + 'psi:' + str(psi) + ', phi:' + str(phi) + ', the:' + str(the) + ', '
        if csize!=None:
            strout = strout + 'cluster_size:' + str(csize)
        strout = strout + ')'

        print(strout)


class ParamsGenTarget():
    def __init__(self):
        self.path_objl = str()
        self.path_initial_vol = str()
        self.tomo_size = (int(), int(), int()) # (dimZ,dimY,dimX)
        self.strategy = str()
        self.radius_list = [int()]
        self.path_mask_list = [str()]
        self.path_target = str()

    def write(self, filename):
        root = ET.Element('paramsGenerateTarget')

        p = ET.SubElement(root, 'path_objl')
        p.set('path', str(self.path_objl))

        p = ET.SubElement(root, 'path_initial_vol')
        p.set('path', str(self.path_initial_vol))

        p = ET.SubElement(root, 'tomo_size')
        pp = ET.SubElement(p, 'X')
        pp.set('size', str(self.tomo_size[2]))
        pp = ET.SubElement(p, 'Y')
        pp.set('size', str(self.tomo_size[1]))
        pp = ET.SubElement(p, 'Z')
        pp.set('size', str(self.tomo_size[0]))

        p = ET.SubElement(root, 'strategy')
        p.set('strategy', str(self.strategy))

        p = ET.SubElement(root, 'radius_list')
        for idx in range(len(self.radius_list)):
            pp = ET.SubElement(p, 'class' + str(idx + 1))
            pp.set('radius', str(self.radius_list[idx]))

        p = ET.SubElement(root, 'path_mask_list')
        for idx in range(len(self.path_mask_list)):
            pp = ET.SubElement(p, 'class'+str(idx + 1))
            pp.set('path', str(self.path_mask_list[idx]))

        p = ET.SubElement(root, 'path_target')
        p.set('path', str(self.path_target))

        tree = ET.ElementTree(root)
        tree.write(filename)


class ParamsTrain():
    def __init__(self):
        self.path_out = str()
        self.path_tomo = [str()]
        self.path_target = [str()]
        self.path_objl_train = str()
        self.path_objl_valid = str()
        self.Ncl = int()
        self.psize = int()
        self.bsize = int()
        self.nepochs = int()
        self.steps_per_e = int()
        self.steps_per_v = int()
        self.flag_direct_read = bool()
        self.flag_bootstrap = bool()
        self.rnd_shift = int()

    def write(self, filename):
        root = ET.Element('paramsTrain')

        p = ET.SubElement(root, 'path_out')
        p.set('path', str(self.path_out))

        p = ET.SubElement(root, 'path_tomo')
        for idx in range(len(self.path_tomo)):
            pp = ET.SubElement(p, 'tomo' + str(idx))
            pp.set('path', str(self.path_tomo[idx]))

        p = ET.SubElement(root, 'path_target')
        for idx in range(len(self.path_target)):
            pp = ET.SubElement(p, 'target' + str(idx))
            pp.set('path', str(self.path_target[idx]))


        p = ET.SubElement(root, 'path_objl_train')
        p.set('path', str(self.path_objl_train))

        p = ET.SubElement(root, 'path_objl_valid')
        p.set('path', str(self.path_objl_valid))

        p = ET.SubElement(root, 'number_of_classes')
        p.set('n', str(self.Ncl))

        p = ET.SubElement(root, 'patch_size')
        p.set('n', str(self.psize))

        p = ET.SubElement(root, 'batch_size')
        p.set('n', str(self.bsize))

        p = ET.SubElement(root, 'number_of_epochs')
        p.set('n', str(self.nepochs))

        p = ET.SubElement(root, 'steps_per_epoch')
        p.set('n', str(self.steps_per_e))

        p = ET.SubElement(root, 'steps_per_validation')
        p.set('n', str(self.steps_per_v))

        p = ET.SubElement(root, 'flag_direct_read')
        p.set('flag', str(self.flag_direct_read))

        p = ET.SubElement(root, 'flag_bootstrap')
        p.set('flag', str(self.flag_bootstrap))

        p = ET.SubElement(root, 'random_shift')
        p.set('shift', str(self.rnd_shift))

        tree = ET.ElementTree(root)
        tree.write(filename)
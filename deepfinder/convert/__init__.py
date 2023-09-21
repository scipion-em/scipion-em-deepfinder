import xml.etree.ElementTree as ET

from deepfinder.constants import *


def objl_read(filename):
    tree = ET.parse(filename)
    objl_xml = tree.getroot()

    objl = []
    for p in range(len(objl_xml)):
        # Mandatory attributes:
        lbl = int(objl_xml[p].get(DF_LABEL))
        x = float(objl_xml[p].get(DF_COORD_X))
        y = float(objl_xml[p].get(DF_COORD_Y))
        z = float(objl_xml[p].get(DF_COORD_Z))

        # Optional attributes:
        tidx = objl_xml[p].get(DF_TOMO_IDX)
        objid = objl_xml[p].get(DF_OBJ_ID)
        psi = objl_xml[p].get(DF_PSI)
        phi = objl_xml[p].get(DF_PHI)
        the = objl_xml[p].get(DF_THETA)
        csize = objl_xml[p].get(DF_SCORE)

        # if optional attributes exist, then cast to correct type:
        if tidx is not None:
            tidx = int(tidx)
        if objid is not None:
            objid = int(objid)
        if csize is not None:
            csize = int(csize)
        if psi is not None or phi is not None or the is not None:
            psi = float(psi)
            phi = float(phi)
            the = float(the)

        obj = {
            DF_TOMO_IDX: tidx,
            DF_OBJ_ID: objid,
            DF_LABEL: lbl,
            DF_COORD_X: x,
            DF_COORD_Y: y,
            DF_COORD_Z: z,
            DF_PSI: phi,
            DF_PHI: psi,
            DF_THETA: the,
            DF_SCORE: csize
        }

        objl.append(obj)
    return objl


def objl_write(objl, filename):
    objl_xml = ET.Element('objlist')
    for idx in range(len(objl)):
        tidx = objl[idx][DF_TOMO_IDX]
        objid = objl[idx][DF_OBJ_ID]
        lbl = objl[idx][DF_LABEL]
        x = objl[idx][DF_COORD_X]
        y = objl[idx][DF_COORD_Y]
        z = objl[idx][DF_COORD_Z]
        psi = objl[idx][DF_PSI]
        phi = objl[idx][DF_PHI]
        the = objl[idx][DF_THETA]
        csize = objl[idx][DF_SCORE]

        obj = ET.SubElement(objl_xml, 'object')
        if tidx is not None:
            obj.set(DF_TOMO_IDX, str(tidx))
        if objid is not None:
            obj.set(DF_OBJ_ID, str(objid))
        obj.set(DF_LABEL, str(lbl))
        obj.set(DF_COORD_X, '%.3f' % x)
        obj.set(DF_COORD_Y, '%.3f' % y)
        obj.set(DF_COORD_Z, '%.3f' % z)
        if psi is not None:
            obj.set(DF_PSI, '%.3f' % psi)
        if phi is not None:
            obj.set(DF_PHI, '%.3f' % phi)
        if the is not None:
            obj.set(DF_THETA, '%.3f' % the)
        if csize is not None:
            obj.set(DF_SCORE, str(csize))

    tree = ET.ElementTree(objl_xml)
    tree.write(filename)


def objl_add(objl, label, coord, obj_id=None, tomo_idx=None, orient=(None, None, None), cluster_size=None):
    obj = {
        DF_TOMO_IDX: tomo_idx,
        DF_OBJ_ID: obj_id,
        DF_LABEL: label,
        DF_COORD_X: coord[2],
        DF_COORD_Y: coord[1],
        DF_COORD_Z: coord[0],
        DF_PSI: orient[0],
        DF_PHI: orient[1],
        DF_THETA: orient[2],
        DF_SCORE: cluster_size
    }
    objl.append(obj)
    return objl


def objl_get_labels(objl):
    """
    Returns a list with different (unique) labels contained in input objl
    """
    class_list = []
    for idx in range(len(objl)):
        class_list.append(objl[idx][DF_LABEL])
    # Set only stores a value once even if it is inserted more then once:
    lbl_set = set(class_list)  # insert the list to the set
    lbl_list = (list(lbl_set))  # convert the set to the list
    return lbl_list


def objl_get_class(objl, label):
    """
    Get all objects of specified class.

    Args:
        objl (list of dict)
        label (int)
    Returns:
        list of dict: contains only objects from class DF_LABEL
    """
    idx_class = []
    for idx in range(len(objl)):
        if str(objl[idx][DF_LABEL]) == str(label):
            idx_class.append(idx)

    objlOUT = []
    for idx in range(len(idx_class)):
        objlOUT.append(objl[idx_class[idx]])
    return objlOUT


class ParamsGenTarget:
    def __init__(self):
        self.path_objl = str()
        self.path_initial_vol = str()
        self.tomo_size = (int(), int(), int())  # (dimZ,dimY,dimX)
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
            pp = ET.SubElement(p, 'class' + str(idx + 1))
            pp.set('path', str(self.path_mask_list[idx]))

        p = ET.SubElement(root, 'path_target')
        p.set('path', str(self.path_target))

        tree = ET.ElementTree(root)
        tree.write(filename)


class ParamsTrain:
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

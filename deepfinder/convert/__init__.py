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
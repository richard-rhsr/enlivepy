from copy import deepcopy
from lxml.html import fromstring
from lxml import etree

import lxml

#@deftemplate("t2.hmtl")
#def main_header(dom, hdr, para_txt, li_items):
#    select("h1", content(hdr))
#    select("div#d1 p", content(para_txt))
#    select("div ul.l li", content(para_txt))


#to transform some data returns back the dom again
#at(dom, "div ul.l", (content ["one", "two"]))

#like at but a little bit different
#sniptest("<html><body><span>Hello </span>", "span", append("World"))


#@defsnippet()
#def header_section(dom):
#    pass

def select(node, selector_str):
    """
    Selector util
    :param node:
    :param selector_str:
    :return:
    """
    found_node = node.cssselect(selector_str)
    if not found_node:
        raise Exception("{} not found in node ".format(selector_str))

    return found_node

#there will be some helper functions like content, append
#wrap, set_attr, remove_attr
def transform(node, selector_str, fn):
    """
    This is the main transform function the transform fn
    should get node and return node back

    :param node:
    :param selector_str:
    :param fn:
    :return:
    """
    found_node = select(node, selector_str)

    #it can be a mutable operation here
    for n in found_node:
        fn(n)

    return node



def at(node_nodes, *args):
    """
    This function gets the node and passes to
    selector transformer pairs the *args should
    be in form like :

    div.css_cls transform_fn
    #myid other_transform_fn

    :param node:
    :param args:
    :return: back the node changed
    """
    if not isinstance(node_nodes, list):
        node_nodes = [node_nodes]

    if len(args) % 2 != 0:
        raise Exception("invalid number of args passed")

    for pair in zip(args[::2], args[1::2]):
        for node in node_nodes:
            if not pair[1]:
                #if the second one is None it
                #means we will have to remove that one
                del_nodes = select(node, pair[0])
                for dnode in del_nodes:
                    dnode.drop_tree()
            else:
                node = transform(node, pair[0], pair[1])

    return node_nodes




def clone_for(iter_obj, transform_fn):

    def _clone_for(node):
        parent = node.getparent()
        if not etree.iselement(parent):
            raise Exception("Can not use after on a root element")

        results = []

        for obj in iter_obj:
            real_transform_fn = transform_fn(obj)
            tmp_node = deepcopy(node)
            tmp_node = real_transform_fn(tmp_node)

            results.append(tmp_node)

        #at this stage we should remove the real one and copy the new
        #ones on its place
        index = parent.index(node)
        for res in reversed(results):
            parent.insert(index, res)

        #drop the real tree please
        node.drop_tree()

        return parent

    return _clone_for



def content(*args, **kwargs):
    """
    Replaces content and returns back a new fn
    :param node:
    :param selector:
    :return:

    TODO more good str operations to e added
    """
    def _content(node):
        #first should remove its children
        for ch in node:
            ch.drop_tree()

        #then we should replace the content
        node.text = ""

        prev = None
        for arg in args:
            if isinstance(arg, basestring):
                if isinstance(prev, lxml.etree._Element):
                    prev.tail = arg
                else:
                    node.text = node.text + arg
            elif isinstance(arg, lxml.etree._Element):
                node.append(arg)
            else:
                raise Exception("invalid type passed to content")

            prev = arg

        return node

    return _content


def append(*args):
    """
    Appends content and returns back a new fn
    :param node:
    :param selector:
    :return:

    TODO more good str operations to e added
    """
    def _append(node):
        prev = None
        for arg in args:
            if isinstance(arg, basestring):
                if isinstance(prev, lxml.etree._Element):
                    prev.tail = arg
                else:
                    node.text = node.text + arg
            elif isinstance(arg, lxml.etree._Element):
                node.append(arg)
            else:
                raise Exception("invalid type passed to content")

            prev = arg

        return node

    return _append


class PrependTransform(object):
    """
    That is another way to create transformer
    if needed of course ...
    """

    def __init__(self, *args):
        self.args = args


    def prepend(self, node):
        for arg in reversed(self.args):
            if isinstance(arg, basestring):
                node.text = arg + node.text
            elif isinstance(arg, lxml.etree._Element):
                node.insert(0, arg)
            else:
                raise Exception("invalid type passed to content")

        return node


    def __call__(self, node):
        return self.prepend(node)



def prepend(*args):
    """
    Appends content and returns back a new fn
    :param node:
    :param selector:
    :return:

    TODO more good str operations to e added
    """
    return PrependTransform(*args)


def after(*args):
    """
    Adds the args
    :param args:
    :return:
    """

    def _after(node):
        parent = node.getparent()
        if not etree.iselement(parent):
            raise Exception("Can not use after on a root element")

        node_index = parent.index(node)

        for arg in reversed(args):
            if isinstance(arg, basestring):
                node.tail = node.tail + arg
            elif isinstance(arg, lxml.etree._Element):
                parent.insert(node_index+1, arg)
            else:
                raise Exception("invalid type passed to content")

        return node

    return _after


class BeforeTranform(object):

    def __init__(self, *args):
        self.args = args


    def before(self, node):

        parent = node.getparent()
        if not etree.iselement(parent):
            raise Exception("Can not use before on a root element")

        node_index = parent.index(node)

        for arg in reversed(self.args):
            if isinstance(arg, basestring):
                prev_node = node.getprevious()
                if not etree.iselement(prev_node):
                    parent.text = arg
                else:
                    prev_node.tail = arg
            elif isinstance(arg, lxml.etree._Element):
                parent.insert(node_index, arg)
            else:
                raise Exception("invalid type passed to content")

        return node


    def __call__(self, node):
        return self.before(node)




def before(*args):
    """
    Puts the args before selection
    :param args:
    :return:
    """
    return BeforeTranform(*args)


class SubstituteTransform(BeforeTranform):

    def __call__(self, node):
        self.before(node)
        node.drop_tree()


def substitute(*args):
    """
    :param args:
    :return:
    """
    return SubstituteTransform(*args)



def wrap(tag_name, **attrs):

    def _wrap(node):

        parent = node.getparent()
        if not etree.iselement(parent):
            raise Exception("Can not use after on a root element")

        el = etree.Element(tag_name, attrs)
        tmp_node = deepcopy(node)
        el.insert(0, tmp_node)

        index = parent.index(node)
        parent.insert(index, el)

        node.drop_tree()

        return el

    return _wrap


def unwrap(node):
    parent = node.getparent()
    if not etree.iselement(parent):
        raise Exception("Can not use after on a root element")

    if len(node) == 0:
        raise Exception("Nothing to unwarp")

    #the next step is ti get its children
    node_copy = deepcopy(node)
    index = parent.index(node)

    for child in reversed(list(node_copy)):
        parent.insert(index, child)

    #remove the old now
    node.drop_tree()

    return parent


def set_attr(**attrs):
    def _set_attr(node):
        attributes = node.attrib
        attributes.update(attrs)

        return node

    return _set_attr

def remove_attr(*attrs):
    def _remove_attr(node):
        attributes = node.attrib
        for a in attrs:
            del attributes[a]

        return node

    return _remove_attr


def add_class(*cls):

    def _add_class(node):
        node_classes = node.attrib.get("class")
        if not node_classes:
            node_classes = set()
        else:
            node_classes = set(node_classes.split())

        for cl in cls:
            if cl in node_classes:
                continue

            node_classes.add(cl)

        node.attrib["class"] = " ".join(list(node_classes))

        return node

    return _add_class


def remove_class(*cls):

    def _remove_class(node):
        node_classes = node.attrib.get("class")
        if not node_classes:
            node_classes = set()
        else:
            node_classes = set(node_classes.split())

        for cl in cls:
            if not cl in node_classes:
                continue

            node_classes.remove(cl)

        node.attrib["class"] = " ".join(list(node_classes))

        return node

    return _remove_class


def do(*tfns):
    def _do(node):
        cnode = node
        for tfn in tfns:
            cnode = tfn(cnode)

        return cnode

    return _do


def emit(nodes, pretty_print=True, first=False):
    if not isinstance(nodes, list):
        nodes = [nodes]

    if first:
        return etree.tostring(nodes[0], pretty_print=pretty_print)

    res = ""
    for n in nodes:
        res = "\n".join([res, etree.tostring(n, pretty_print=pretty_print)])

    return res


def move(src_select, dest_select, combiner):
    """
    TODO implement it
    :param src_select:
    :param dest_select:
    :param combiner:
    :return:
    """
    pass



def identity(node):
    return node


if __name__ == "__main__":
    pass

from state.db.persistent_db import PersistentDB
from state.trie.pruning_trie import Trie, rlp_encode, bin_to_nibbles, \
    NODE_TYPE_LEAF, NODE_TYPE_EXTENSION, unpack_to_nibbles, \
    without_terminator, BLANK_NODE
from state.util.utils import to_string
from storage.kv_in_memory import KeyValueStorageInMemory


def test_get_prefix_nodes():
    trie = Trie(PersistentDB(KeyValueStorageInMemory()))
    prefix = 'abcd'
    prefix_nibbles = bin_to_nibbles(to_string(prefix))
    key1 = prefix + '1'
    key2 = prefix + '2'
    key3 = prefix + '3'
    trie.update(key1.encode(), rlp_encode(['v1']))
    seen_prefix = []
    last_node = trie._get_last_node_for_prfx(trie.root_node, prefix_nibbles,
                                             seen_prfx=seen_prefix)
    # The last node should be a leaf since only 1 key
    assert trie._get_node_type(last_node) == NODE_TYPE_LEAF
    # Seen prefix matches the prefix exactly
    assert seen_prefix == prefix_nibbles

    # The queried key is larger than prefix, results in blank node
    last_node_ = trie._get_last_node_for_prfx(trie.root_node,
                                              bin_to_nibbles(to_string(prefix + '5')), [])
    assert last_node_ == BLANK_NODE

    seen_prefix = []
    trie.update(key2.encode(), rlp_encode(['v2']))
    last_node = trie._get_last_node_for_prfx(trie.root_node, prefix_nibbles,
                                             seen_prfx=seen_prefix)
    # The last node should be an extension since more than 1 key
    assert trie._get_node_type(last_node) == NODE_TYPE_EXTENSION
    assert seen_prefix == unpack_to_nibbles(last_node[0])

    seen_prefix = []
    trie.update(key3.encode(), rlp_encode(['v3']))
    last_node = trie._get_last_node_for_prfx(trie.root_node, prefix_nibbles,
                                             seen_prfx=seen_prefix)
    assert trie._get_node_type(last_node) == NODE_TYPE_EXTENSION
    assert seen_prefix == unpack_to_nibbles(last_node[0])

    last_node_key = without_terminator(unpack_to_nibbles(last_node[0]))
    # Key for the fetched prefix nodes (ignore last nibble) is same as prefix nibbles
    assert last_node_key[:-1] == prefix_nibbles

    # The extension node is correctly decoded.
    decoded_extension = trie._decode_to_node(last_node[1])
    assert decoded_extension[1] == [b' ', rlp_encode(['v1'])]
    assert decoded_extension[2] == [b' ', rlp_encode(['v2'])]
    assert decoded_extension[3] == [b' ', rlp_encode(['v3'])]
.. include:: global.rst

Example - Threadsafe Radio Operations
====================

Differences from Original :func:`~RFM69.Radio` Class
----------
The :func:`~RFM69.RadioThreadSafe` class is identical to the :func:`~RFM69.Radio` class, with three exceptions:

#. The class is threadsafe, so no race conditions should occur
#. The ``packets`` member has been removed
#. The class has a new :func:`~RFM69.RadioThreadSafe.get_packet` method, which allows threaded code to block until a packet is avaialble (without having to loop or call ``time.sleep(timeout)``.


Simple Transceiver
------------------
Here's the simple transceiver example adapted to use the threadsafe interface. Notice how the timing code is much cleaner since the call to :func:`~RFM69.RadioThreadSafe.get_packet` takes care of part of the timing out for us.

.. literalinclude:: ../../examples/example_rxtx_threadsafe.py
   :language: python


Better Transceiver
------------------
Here's an even better way to use the threadsafe interface: start up a separate thread to handle incoming packets. Now we've eliminated the original complex timing code altogether, and the result is much more readable.

.. literalinclude:: ../../examples/example_rxtx_threadsafe_advanced.py
   :language: python

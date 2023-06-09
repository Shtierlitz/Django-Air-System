const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
const hostname = window.location.hostname;
const port = window.location.port;
const socketUrl = `${protocol}//${hostname}:${port}/ws/status_updates/`;
console.log(socketUrl, "урла 1")

const socket = new WebSocket(socketUrl);
console.log(socketUrl, "урла 2")
        // Listen for messages
        socket.addEventListener('message', (event) => {
            console.log('WebSocket message received:', event);
            const data = JSON.parse(event.data);

            if (data.ticket_id && data.check_in) {
                updateTicketStatus(data.ticket_id, data.check_in, 'check_in');
            }
            if (data.ticket_id && data.onboard) {
                updateTicketStatus(data.ticket_id, data.onboard, 'onboard');
            }
        });

        // Listen for messages
        socket.addEventListener('message', (event) => {
            console.log('WebSocket message received:', event);
            const data = JSON.parse(event.data);

            if (data.ticket_id && data.check_in) {
                updateTicketStatus(data.ticket_id, data.check_in);
            }
        });

        // Update the ticket status in the UI
        function updateTicketStatus(ticket_id, status, status_type) {
            // Find the HTML element that displays the ticket status
            const ticketStatusElement = document.querySelector(`#ticket-${ticket_id}-${status_type}-status`);

            // Update the status text and color
            if (ticketStatusElement) {
                ticketStatusElement.textContent = status;
                if (status === 'NOT APPROVED') {
                    ticketStatusElement.style.color = 'red';
                } else if (status === 'APPROVED') {
                    ticketStatusElement.style.color = 'green';
                }
            }
        }
import React from 'react';
import InfoForm from '../components/infoForm.js'
class ContactSection extends React.Component {

	constructor(props) {
		super(props);
		this.state = {
			name: props.name,
			phone: props.phone,
			email: props.email,
			message: props.message
		}

		this.storeInfo = this.storeInfo.bind(this)
	}
	storeInfo(info, el) {
		this.setState({ ...info });
		console.log(this.state)
	}
	render() {
		return (
			<div className="d-flex flex-column flex-wrap">
				<h1 class="my-4">
					Your New Project Starts Here
				</h1>
				<InfoForm value={this.state} update={this.storeInfo} buttonName='Contact Us' header={`Contact us to learn more, or check out our online quote builder.`} />
			</div>
		);
	}

}

export default ContactSection;

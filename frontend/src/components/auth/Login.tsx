import React, { useState } from 'react';
import styles from './Login.module.css';

const qrCode = '/qr-code.png';

function Login() {
    return (
        <div className={styles.container}>
            <img className={styles.qrCode} src={qrCode}/>
            <h1>Log in to Message2 by QR Code</h1>
            <div className={styles.instructions}>
                <p>1. Open Message2 on your phone</p>
                <p>2. Go to <strong>Settings &gt; Devices &gt; Link Desktop Device</strong></p>
                <p>3. Point your phone at this screen to confirm login</p>
            </div>
            <div className={styles.buttons}>
                <button>LOG IN BY PHONE NUMBER</button>
                <button>LOG IN BY PASSKEY</button>
                <button>ПРОДОЛЖИТЬ НА РУССКОМ</button>
            </div>
        </div>
    );
}

export default Login;